"""Modelo cinemático didático; JSON/tópico simulado, NÃO broker MQTT real."""
import json,math,csv
from pathlib import Path
from dataclasses import asdict
from inference import RuleEngine,real_availability
from policy_native import NativePolicy
ROOT=Path(__file__).resolve().parents[1]
TOPIC='carrinho/joystick'
def clamp(x):return max(-255,min(255,x))
def parse_message(topic,payload):
    if topic!=TOPIC:raise ValueError('Tópico incorreto')
    data=json.loads(payload)
    if not isinstance(data,dict) or any(type(data.get(k)) is not int or not -255<=data[k]<=255 for k in ('x','y')):raise ValueError('JSON x/y inválido')
    return data['x'],data['y']
class Simulation:
    def __init__(self,mode='A',engine=None):
        self.policy=NativePolicy();self.mode=mode;self.reason='';self.engine=engine
        if self.engine is None:
            if mode=='A':self.engine=RuleEngine()
            else:self.engine,self.reason=real_availability()
        self.reset()
    def reset(self):
        self.time_ms=0;self.last_command=0;self.last_prediction=0;self.command_ok=False
        self.x=self.y=0;self.position=0.;self.heading=0.;self.obstacle=120.;self.window=[]
        self.left=self.right=0;self.label='DESCONHECIDO';self.confidence=None;self.probabilities={};self.inference_ms=0
        self.prediction_ok=False;self.connected=True;self.invalid_sensor=False;self.low_confidence_fault=False
        self.reverse_allowed=True;self.sign=1;self.sensor_elapsed=0;self.distance=120.;self.trace=[];self.collisions=0;self.replay=None;self.replay_index=0
    def receive(self,topic,payload):
        try:self.x,self.y=parse_message(topic,payload)
        except (ValueError,TypeError):self.command_ok=False;self.left=self.right=0;return False
        if not self.connected:return False
        self.last_command=self.time_ms;self.command_ok=True;return True
    def set_distance(self,d):
        if not math.isfinite(d) or not 2<=d<=400:raise ValueError('Distância entre 2 e 400 cm')
        self.obstacle=self.position+d;self.replay=None
    def invalidate(self,reason):
        self.reason=reason;self.window=[];self.prediction_ok=False;self.label='DESCONHECIDO';self.confidence=None;self.probabilities={};self.left=self.right=0
    def sensor(self,d):
        self.distance=d
        if not math.isfinite(d) or not 2<=d<=400:self.invalidate('Leitura inválida simulada');return
        self.window.append(float(d))
        if len(self.window)<10:return
        frame=self.window;self.window=[]
        if self.engine is None:self.invalidate('Modo B indisponível: modelo/runtime ausente');return
        try:p=self.engine.predict(frame)
        except Exception as e:self.invalidate('Falha de inferência: '+str(e));return
        self.label=p.label;self.confidence=p.confidence;self.probabilities=p.probabilities;self.inference_ms=p.elapsed_ms;self.last_prediction=self.time_ms
        self.prediction_ok=self.label in {'LIVRE','ATENCAO','PERIGO'} and (self.confidence is None or (math.isfinite(self.confidence) and self.confidence>=0.80))
        self.reason='OK' if self.prediction_ok else 'Baixa confiança real / classe desconhecida'
    def actuate(self):
        healthy=self.connected and self.command_ok and self.prediction_ok and not self.invalid_sensor and not self.low_confidence_fault and self.policy.fresh(self.time_ms,self.last_command,350) and self.policy.fresh(self.time_ms,self.last_prediction,1800)
        self.left,self.right=self.policy.gate(clamp(self.y+self.x),clamp(self.y-self.x),self.label,healthy,self.reverse_allowed,self.sign)
        if self.low_confidence_fault:self.reason='Falha injetada: confiança insuficiente (não altera saída real)'
        elif not self.connected:self.reason='Conexão simulada perdida'
        elif self.command_ok and not self.policy.fresh(self.time_ms,self.last_command,350):self.reason='Timeout de comando'
    def step(self,dt=0.05):
        if not 0<dt<=0.15:raise ValueError('Passo deve ser <=150ms')
        self.time_ms+=round(dt*1000);self.sensor_elapsed+=round(dt*1000)
        if self.sensor_elapsed>=150:
            self.sensor_elapsed-=150
            if self.invalid_sensor:d=float('nan')
            elif self.replay:
                d=self.replay[self.replay_index%len(self.replay)];self.replay_index+=1;self.obstacle=self.position+d
            else:d=self.obstacle-self.position
            self.sensor(d)
        self.actuate()
        # Velocidade linear ideal 30cm/s por PWM máximo, sem física elétrica/inércia.
        speed=(self.left+self.right)/2/255*30*self.sign
        self.position+=speed*dt;self.heading+=(self.right-self.left)/255*dt
        if self.position>self.obstacle-2:
            self.position=self.obstacle-2;self.collisions+=1
        state=self.snapshot();self.trace.append(state);return state
    def snapshot(self):
        return {'tempo_ms':self.time_ms,'modo':self.mode,'comunicacao':'JSON SIMULADO, sem broker MQTT','distancia_cm':self.distance if math.isfinite(self.distance) else None,
                'x':self.x,'y':self.y,'classe':self.label,'confianca':self.confidence,'probabilidades':self.probabilities.copy(),'infer_ms':self.inference_ms,
                'DD':self.right,'TD':self.right,'DE':self.left,'TE':self.left,'posicao_cm':self.position,'heading_rad':self.heading,'motivo':self.reason,'colisoes_simuladas':self.collisions}
    def use_dataset(self,label):
        rows=list(csv.DictReader((ROOT/'dataset/dados_simulados_cp2.csv').open(encoding='utf-8-sig')))
        self.replay=[float(r['distancia_cm']) for r in rows if r['classe']==label];self.replay_index=0
    def export(self,path):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'aviso':'SIMULAÇÃO; não é validação física','trace':self.trace},indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
SCENARIOS=['LIVRE','ATENCAO','PERIGO','APROXIMACAO','RE','SENSOR_INVALIDO','BAIXA_CONFIANCA','SEM_CONEXAO']
def run_scenario(name,mode='A',seconds=6):
    if name not in SCENARIOS:raise ValueError(name)
    sim=Simulation(mode);sim.obstacle=300
    if name in ('LIVRE','ATENCAO','PERIGO'):sim.use_dataset(name)
    elif name=='RE':sim.use_dataset('PERIGO')
    else:sim.use_dataset('LIVRE')
    for i in range(round(seconds/0.05)):
        if name=='APROXIMACAO':
            sim.replay=None;sim.obstacle=sim.position+max(10,120-i*1.0)
        if sim.time_ms>=2500:
            if name=='SENSOR_INVALIDO':sim.invalid_sensor=True
            if name=='BAIXA_CONFIANCA':sim.low_confidence_fault=True
            if name=='SEM_CONEXAO':sim.connected=False
        y=-200 if name=='RE' else 200
        if sim.connected:sim.receive(TOPIC,json.dumps({'x':0,'y':y}))
        sim.step()
    return sim

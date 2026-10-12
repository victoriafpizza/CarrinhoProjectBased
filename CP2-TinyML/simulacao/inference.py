"""A = regras explícitas. B = ONNX REAL exportado do Edge Impulse; sem fallback."""
from dataclasses import dataclass
from pathlib import Path
import hashlib,json,math,time
ROOT=Path(__file__).resolve().parents[1]
@dataclass
class Prediction:
    label:str
    confidence:float|None
    probabilities:dict
    elapsed_ms:float=0
class RuleEngine:
    mode='A — REGRAS, SEM MACHINE LEARNING'
    def predict(self,window):
        if len(window)!=10 or any(not math.isfinite(x) or not 2<=x<=400 for x in window):raise ValueError('Janela inválida')
        d=window[-1]
        return Prediction('PERIGO' if d<25 else 'ATENCAO' if d<=60 else 'LIVRE',None,{})
class EdgeImpulseONNX:
    mode='B — MODELO REAL EDGE IMPULSE / ONNX CPU'
    def __init__(self,manifest=None):
        import numpy as np
        import onnxruntime as ort
        manifest=Path(manifest or ROOT/'modelo/desktop/model.json')
        m=json.loads(manifest.read_text(encoding='utf-8'));model=manifest.parent/m['arquivo']
        if hashlib.sha256(model.read_bytes()).hexdigest()!=m['sha256']:raise RuntimeError('Hash do ONNX não confere')
        if m.get('origem')!='Edge Impulse' or m.get('scale_axes')!=1 or len(m['labels'])!=3 or m['input_size']!=10:raise RuntimeError('Metadados incompatíveis com pipeline Raw Data')
        self.np=np;self.labels=m['labels'];self.session=ort.InferenceSession(str(model),providers=['CPUExecutionProvider'])
        self.input=self.session.get_inputs()[0];self.output=self.session.get_outputs()[0];self.manifest=m
        if self.input.type!='tensor(float)':raise RuntimeError('Adaptador exige ONNX float32')
    def predict(self,window):
        if len(window)!=10 or any(not math.isfinite(x) or not 2<=x<=400 for x in window):raise ValueError('Janela inválida')
        data=self.np.asarray(window,dtype=self.np.float32).reshape(1,10)
        t=time.perf_counter();values=self.session.run([self.output.name],{self.input.name:data})[0].reshape(-1)
        if len(values)!=3 or any(not math.isfinite(float(v)) or not 0<=float(v)<=1 for v in values) or abs(float(values.sum())-1)>0.01:raise RuntimeError('Probabilidades inválidas do runtime')
        probabilities={c:float(v) for c,v in zip(self.labels,values)};label=max(probabilities,key=probabilities.get)
        return Prediction(label,probabilities[label],probabilities,(time.perf_counter()-t)*1000)
def real_availability():
    try:return EdgeImpulseONNX(),''
    except (ImportError,OSError,ValueError,RuntimeError,KeyError) as e:return None,str(e)

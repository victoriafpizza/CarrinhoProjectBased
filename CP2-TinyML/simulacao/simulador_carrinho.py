"""GUI Tkinter + modo headless reproduzível. Não depende de ESP32 ou pilhas."""
import argparse,json,time
from pathlib import Path
from core import Simulation,SCENARIOS,run_scenario,TOPIC,ROOT
def main():
    p=argparse.ArgumentParser();p.add_argument('--headless',action='store_true');p.add_argument('--mode',choices=['A','B'],default='A');p.add_argument('--cenario',choices=SCENARIOS,default='LIVRE');p.add_argument('--saida',type=Path)
    a=p.parse_args()
    if a.headless:
        sim=run_scenario(a.cenario,a.mode)
        if a.saida:sim.export(a.saida)
        print(json.dumps(sim.snapshot(),ensure_ascii=False));return 2 if sim.engine is None else 0
    import tkinter as tk
    from tkinter import ttk,messagebox
    root=tk.Tk();root.title('CP2 | Carrinho 4WD — SIMULAÇÃO, não teste físico');root.geometry('1120x800')
    App(root,a.mode);root.mainloop();return 0
class App:
    def __init__(self,root,mode='A'):
        import tkinter as tk
        from tkinter import ttk,messagebox
        self.root=root;self.sim=Simulation(mode);self.auto=None;self.auto_start=0;self.paused=False
        root.configure(bg='#101827');self.vars={};self.colors={'LIVRE':'#34d399','ATENCAO':'#fbbf24','PERIGO':'#f87171','DESCONHECIDO':'#94a3b8'}
        top=ttk.Frame(root,padding=12);top.pack(fill='x')
        ttk.Label(top,text='CP2 • TinyML / ESP32 / 4WD',font=('Segoe UI',18,'bold')).pack(side='left')
        self.mode=tk.StringVar(value=mode);combo=ttk.Combobox(top,textvariable=self.mode,values=['A','B'],state='readonly',width=5);combo.pack(side='right');combo.bind('<<ComboboxSelected>>',self.change_mode)
        self.banner=tk.Label(root,text='',bg='#1e293b',fg='white',font=('Segoe UI',11),pady=10);self.banner.pack(fill='x')
        mid=ttk.Frame(root);mid.pack(fill='both',expand=True)
        controls=ttk.Frame(mid,padding=12);controls.pack(side='left',fill='y')
        ttk.Label(controls,text='Joystick: W/A/S/D ou setas',font=('Segoe UI',11,'bold')).pack(anchor='w')
        self.x=tk.IntVar(value=0);self.y=tk.IntVar(value=0)
        for text,var in [('X — curva',self.x),('Y — avanço / ré',self.y)]:
            ttk.Label(controls,text=text).pack(anchor='w');tk.Scale(controls,from_=-255,to=255,orient='horizontal',variable=var,length=260).pack()
        ttk.Button(controls,text='Parar joystick (espaço)',command=lambda:(self.x.set(0),self.y.set(0))).pack(fill='x',pady=5)
        ttk.Label(controls,text='Distância manual do obstáculo (cm)').pack(anchor='w')
        self.dist=tk.DoubleVar(value=120);tk.Scale(controls,from_=2,to=400,resolution=1,orient='horizontal',variable=self.dist,length=260,command=self.distance_changed).pack()
        self.scenario=tk.StringVar(value='LIVRE');ttk.Combobox(controls,textvariable=self.scenario,values=SCENARIOS,state='readonly').pack(fill='x')
        ttk.Button(controls,text='Executar cenário',command=self.start_scenario).pack(fill='x',pady=5)
        self.fault_vars={}
        for label,name in [('Sensor inválido','invalid_sensor'),('Baixa confiança — falha injetada','low_confidence_fault'),('Perder conexão simulada','disconnect'),('Permitir ré virtual','reverse_allowed')]:
            v=tk.BooleanVar(value=name=='reverse_allowed');self.fault_vars[name]=v;ttk.Checkbutton(controls,text=label,variable=v).pack(anchor='w',pady=4)
        ttk.Button(controls,text='Pausar / continuar',command=self.pause).pack(fill='x',pady=5)
        ttk.Button(controls,text='Reiniciar',command=self.reset).pack(fill='x')
        ttk.Button(controls,text='Salvar evidência JSON',command=self.save).pack(fill='x',pady=5)
        ttk.Label(controls,text='Comunicação: JSON simulado\nSem broker MQTT real\nDados sintéticos / física ideal',foreground='#9a3412').pack(anchor='w',pady=8)
        right=ttk.Frame(mid);right.pack(side='left',fill='both',expand=True)
        self.canvas=tk.Canvas(right,bg='#101827',highlightthickness=0,height=340);self.canvas.pack(fill='both',expand=True)
        self.details=tk.Label(right,font=('Consolas',12),bg='#1e293b',fg='white',justify='left',anchor='nw',padx=14,pady=12);self.details.pack(fill='x')
        self.graph=tk.Canvas(right,bg='#0f172a',highlightthickness=0,height=140);self.graph.pack(fill='x')
        self.footer=tk.Label(root,text='Iniciando janela de 10 leituras / 150 ms',bg='#101827',fg='#cbd5e1',anchor='w',padx=12,pady=8);self.footer.pack(fill='x')
        for key in ['w','Up','s','Down','a','Left','d','Right','space']:
            root.bind('<KeyPress-'+key+'>',lambda e,k=key:self.key(k,True));root.bind('<KeyRelease-'+key+'>',lambda e,k=key:self.key(k,False))
        root.bind('<FocusOut>',lambda e:(self.x.set(0),self.y.set(0)))
        self.tick()
    def change_mode(self,event=None):
        from tkinter import messagebox
        sim=Simulation(self.mode.get())
        if sim.engine is None:
            messagebox.showinfo('Modo B indisponível',sim.reason);self.mode.set('A');return
        self.sim=sim;self.auto=None
    def key(self,key,pressed):
        if key in ['w','Up']:self.y.set(200 if pressed else 0)
        if key in ['s','Down']:self.y.set(-200 if pressed else 0)
        if key in ['a','Left']:self.x.set(-150 if pressed else 0)
        if key in ['d','Right']:self.x.set(150 if pressed else 0)
        if key=='space':self.x.set(0);self.y.set(0)
    def distance_changed(self,value):
        self.auto=None;self.sim.set_distance(float(value))
    def pause(self):self.paused=not self.paused
    def reset(self):self.sim.reset();self.auto=None;self.x.set(0);self.y.set(0)
    def start_scenario(self):
        self.sim.reset();self.auto=self.scenario.get();self.auto_start=self.sim.time_ms;self.sim.obstacle=300
        for name,var in self.fault_vars.items():var.set(name=='reverse_allowed')
        self.x.set(0);self.y.set(-200 if self.auto=='RE' else 200)
        self.sim.use_dataset(self.auto if self.auto in ('LIVRE','ATENCAO','PERIGO') else 'PERIGO' if self.auto=='RE' else 'LIVRE')
    def save(self):
        from tkinter import messagebox
        path=ROOT/'evidencias/simulacao'/('gui_'+time.strftime('%Y%m%d_%H%M%S')+'.json');self.sim.export(path)
        messagebox.showinfo('Evidência simulada salva',str(path))
    def tick(self):
        if not self.paused:
            if self.auto=='APROXIMACAO':self.sim.replay=None;self.sim.obstacle=self.sim.position+max(10,120-(self.sim.time_ms-self.auto_start)/50)
            if self.auto and self.sim.time_ms-self.auto_start>=2500:
                for scenario,flag in [('SENSOR_INVALIDO','invalid_sensor'),('BAIXA_CONFIANCA','low_confidence_fault'),('SEM_CONEXAO','disconnect')]:
                    if self.auto==scenario:self.fault_vars[flag].set(True)
            for name in ['invalid_sensor','low_confidence_fault','reverse_allowed']:setattr(self.sim,name,self.fault_vars[name].get())
            self.sim.connected=not self.fault_vars['disconnect'].get()
            if self.sim.connected:self.sim.receive(TOPIC,json.dumps({'x':self.x.get(),'y':self.y.get()}))
            self.sim.step()
        self.draw();self.root.after(50,self.tick)
    def draw(self):
        s=self.sim.snapshot();c=self.colors[s['classe']];canvas=self.canvas;canvas.delete('all');w=max(canvas.winfo_width(),680);h=max(canvas.winfo_height(),280)
        self.banner.configure(text=(self.sim.engine.mode if self.sim.engine else 'MODO B INDISPONÍVEL')+' | SIMULAÇÃO • SEM HARDWARE',fg=c)
        canvas.create_text(24,25,text='Sensor virtual → janela → decisão → quatro motores',fill='#cbd5e1',anchor='w',font=('Segoe UI',12))
        canvas.create_line(25,h*.62,w-25,h*.62,fill='#334155',width=3)
        px=100;py=h*.55;d=s['distancia_cm'];ox=px+90+min(400,d if d is not None else 0)/400*(w-240)
        canvas.create_rectangle(ox,80,ox+20,h*.72,fill='#fb7185',outline='');canvas.create_text(ox,60,text='OBSTÁCULO',fill='#fda4af',font=('Segoe UI',10))
        canvas.create_rectangle(px-48,py-35,px+48,py+35,fill=c,outline='#f8fafc',width=2)
        canvas.create_polygon(px+48,py-15,px+64,py,px+48,py+15,fill=c,outline='#f8fafc')
        for x,y,label,pwm in [(px-36,py-46,'TE',s['TE']),(px+25,py-46,'DE',s['DE']),(px-36,py+35,'TD',s['TD']),(px+25,py+35,'DD',s['DD'])]:
            canvas.create_rectangle(x,y,x+25,y+14,fill='#0f172a',outline='#94a3b8');canvas.create_text(x+12,y-9 if y<py else y+27,text=f'{label} {pwm}',fill='#e2e8f0',font=('Consolas',9))
        canvas.create_line(px+64,py,ox,py,fill='#94a3b8',dash=(4,4));canvas.create_text((px+64+ox)/2,py-20,text=f'{d:.1f} cm' if d is not None else 'LEITURA INVÁLIDA',fill='white')
        # Faixas animadas evidenciam deslocamento com carrinho centralizado.
        for i in range(15):
            mark=(i*70-self.sim.position*4)%w;canvas.create_rectangle(mark,h*.8,mark+24,h*.8+3,fill='#475569',outline='')
        conf='N/A — regras não têm probabilidade' if s['confianca'] is None else f"{s['confianca']*100:.2f}%"
        self.details.configure(text=f"Estado: {s['classe']}   Confiança: {conf}\nJoystick x={s['x']:4} y={s['y']:4}  |  Esquerda DE/TE={s['DE']:4}  Direita DD/TD={s['DD']:4}\nPosição virtual: {s['posicao_cm']:.2f} cm  |  Inferência CPU: {s['infer_ms']:.3f} ms\n{s['motivo']}",fg=c)
        self.footer.configure(text=f"Tempo simulado {s['tempo_ms']/1000:.2f}s | Janela {len(self.sim.window)}/10 | Colisões virtuais: {s['colisoes_simuladas']} | Espaço: parar")
        self.graph.delete('all');gw=max(self.graph.winfo_width(),680);gh=140;self.graph.create_text(12,14,text='PWM solicitado: esquerda (verde) / direita (azul)',anchor='w',fill='#cbd5e1')
        trace=self.sim.trace[-200:]
        if len(trace)>1:
            for key,col in [('DE','#34d399'),('DD','#60a5fa')]:
                points=[v for i,r in enumerate(trace) for v in (12+i*(gw-24)/199,80-r[key]/255*40)];self.graph.create_line(*points,fill=col,width=2)
if __name__=='__main__':raise SystemExit(main())

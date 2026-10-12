"""Uma execução = uma sessão real. Rótulo manual preservado; nunca recalculado."""
import argparse,csv,json,time,math
from pathlib import Path
def main():
    import serial
    p=argparse.ArgumentParser();p.add_argument('--porta',required=True);p.add_argument('--classe',required=True,choices=['LIVRE','ATENCAO','PERIGO'])
    p.add_argument('--saida',required=True,type=Path);p.add_argument('--segundos',type=float,default=30);p.add_argument('--cenario',required=True)
    a=p.parse_args()
    if a.saida.exists():p.error('Use arquivo novo para cada sessão')
    a.saida.parent.mkdir(parents=True,exist_ok=True);n=0;bad=0
    with serial.Serial(a.porta,115200,timeout=1) as ser,a.saida.open('x',newline='',encoding='utf-8') as f:
        time.sleep(2);ser.reset_input_buffer();ser.write({'LIVRE':b'1','ATENCAO':b'2','PERIGO':b'3'}[a.classe]);ser.write(b's')
        w=csv.writer(f);w.writerow(['tempo_ms','distancia_cm','classe']);last=-1;end=time.monotonic()+a.segundos
        try:
            while time.monotonic()<end:
                line=ser.readline().decode('utf-8',errors='replace').strip()
                if not line:continue
                if line.startswith('#'):
                    print(line);bad+=int('INVALID' in line);continue
                try:
                    t,d,c=line.split(',');t=int(t);d=float(d)
                    if not math.isfinite(d) or not 2<=d<=400 or c!=a.classe or t<=last:raise ValueError()
                except ValueError:bad+=1;continue
                w.writerow([t,d,c]);f.flush();last=t;n+=1
        except KeyboardInterrupt:pass
        finally:ser.write(b'p')
    a.saida.with_suffix('.metadata.json').write_text(json.dumps({'fonte':'real','classe':a.classe,'cenario':a.cenario,'validas':n,'invalidas':bad},indent=2),encoding='utf-8')
if __name__=='__main__':main()

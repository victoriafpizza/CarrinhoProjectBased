"""Gera fixture SINTÉTICA nova; nunca substitui dataset fornecido."""
import argparse,csv,random
from pathlib import Path
def generate(path,seed=550609):
    rng=random.Random(seed)
    with Path(path).open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['tempo_ms','distancia_cm','classe']);i=0
        for c,lo,hi in [('LIVRE',61,180),('ATENCAO',25,60),('PERIGO',2,24.9)]:
            for _ in range(150):
                w.writerow([i*150,round(rng.uniform(lo,hi),2),c]);i+=1
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--saida',required=True);p.add_argument('--seed',type=int,default=550609);a=p.parse_args();generate(a.saida,a.seed)

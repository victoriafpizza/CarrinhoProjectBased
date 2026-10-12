"""Valida CSV e exporta amostras EI sem sobreposição. Biblioteca padrão."""
import argparse, csv, hashlib, json, math
from collections import Counter
from pathlib import Path
CLASSES={'LIVRE','ATENCAO','PERIGO'}
def label(d):
    return 'PERIGO' if d<25 else 'ATENCAO' if d<=60 else 'LIVRE'
def validate(path):
    rows=[]; seen=set(); errors=[]
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['tempo_ms','distancia_cm','classe']:
            raise ValueError('Cabeçalho deve ser tempo_ms,distancia_cm,classe')
        for line,r in enumerate(reader,2):
            try:
                t=int(r['tempo_ms']); d=float(r['distancia_cm']); c=r['classe']
                if t<0 or not math.isfinite(d) or not 2<=d<=400 or c not in CLASSES:
                    raise ValueError('faixa/rótulo inválido')
                if label(d)!=c: raise ValueError('rótulo incompatível com limites provisórios')
                key=(t,d,c)
                if key in seen: raise ValueError('linha duplicada')
                if rows and t<=rows[-1][0]: raise ValueError('tempo não crescente: separe sessões')
                seen.add(key); rows.append((t,d,c))
            except (ValueError,TypeError,KeyError) as e:
                errors.append({'linha':line,'erro':str(e)})
    if errors: raise ValueError(json.dumps(errors,ensure_ascii=False))
    if not rows: raise ValueError('CSV vazio')
    return rows
def windows(rows,n=10,tolerance=15):
    runs=[]; run=[]
    for i,r in enumerate(rows):
        if run and (r[2]!=run[-1][1][2] or abs(r[0]-run[-1][1][0]-150)>tolerance):
            runs.append(run); run=[]
        run.append((i,r))
    if run:runs.append(run)
    return [run[i:i+n] for run in runs for i in range(0,len(run)-n+1,n)]
def export(inputs,out,source,split_mode):
    out=Path(out)
    if out.exists(): raise ValueError('Saída já existe; use uma pasta nova para preservar resultados')
    allrows={}; counts=Counter(); assignments=[]
    for path,subset in inputs:
        rows=validate(path); allrows[str(path)]=rows
        counts.update(r[2] for r in rows)
        if split_mode=='temporal':
            # Divide cada trecho de classe ANTES das janelas; purga uma janela na fronteira.
            start=0
            while start<len(rows):
                end=start+1
                while end<len(rows) and rows[end][2]==rows[start][2]:end+=1
                cut=start+int((end-start)*0.8)
                for sub,a,b in [('training',start,cut),('testing',cut+10,end)]:
                    for w in windows(rows[a:b]):
                        assignments.append((path,sub,[(i+a,r) for i,r in w]))
                start=end
        else:
            for w in windows(rows):assignments.append((path,subset,w))
    if set(counts)!=CLASSES:raise ValueError('É necessário coletar as três classes')
    manifest=[]; fingerprints={}
    for k,(path,sub,w) in enumerate(assignments):
        c=w[0][1][2]; vals=[r[1] for _,r in w]
        fp=hashlib.sha256(json.dumps(vals).encode()).hexdigest()
        if fp in fingerprints and fingerprints[fp]!=sub:
            raise ValueError('Janela idêntica nos dois conjuntos')
        fingerprints[fp]=sub
        manifest.append({'arquivo':f"{'treino' if sub=='training' else 'teste'}/{c}.{k:04d}.csv",
                         'subset':sub,'classe':c,'origem':str(path),'linhas':[i+2 for i,_ in w],
                         'tempo_inicial_ms':w[0][1][0],'tempo_final_ms':w[-1][1][0],
                         'distancias':vals,'sha256_janela':fp})
    for sub in ['training','testing']:
        if {m['classe'] for m in manifest if m['subset']==sub}!=CLASSES:
            raise ValueError('Poucas amostras: cada conjunto deve conter as três classes')
    used={s:set() for s in ['training','testing']}
    for m in manifest:
        used[m['subset']].update((m['origem'],i) for i in m['linhas'])
    assert not used['training'] & used['testing']
    out.mkdir(parents=True)
    for m in manifest:
        f=out/m['arquivo'];f.parent.mkdir(exist_ok=True)
        with f.open('w',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream);writer.writerow(['timestamp','distancia_cm'])
            writer.writerows((i*150,d) for i,d in enumerate(m.pop('distancias')))
    report={'fonte':source,'split':split_mode,'intervalo_ms':150,'frequencia_hz':1000/150,
            'leituras_por_janela':10,'duracao_nominal_ms':1500,'ultimo_timestamp_ms':1350,
            'linhas_por_classe':dict(counts),'janelas_por_subset_classe':dict(Counter(m['subset']+'/'+m['classe'] for m in manifest)),
            'sem_linhas_compartilhadas':True,'manifesto':manifest,
            'sha256_entradas':{str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p,_ in inputs},
            'limitacao':'Split temporal com purga reduz proximidade, mas NÃO demonstra independência de sessões.' if split_mode=='temporal' else 'Sessões distintas; garantir também cenários independentes.'}
    (out/'validacao.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    return report
def main():
    p=argparse.ArgumentParser();p.add_argument('--entrada',type=Path);p.add_argument('--treino',nargs='+',type=Path);p.add_argument('--teste',nargs='+',type=Path)
    p.add_argument('--saida',required=True,type=Path);p.add_argument('--fonte',choices=['simulado','real'],required=True)
    a=p.parse_args()
    if a.entrada and not(a.treino or a.teste):
        if a.fonte=='real':p.error('Dados reais exigem --treino e --teste de sessões independentes')
        inputs=[(a.entrada,None)];mode='temporal'
    elif a.treino and a.teste and not a.entrada:
        if set(p.resolve() for p in a.treino)&set(p.resolve() for p in a.teste):p.error('Mesma sessão nos dois conjuntos')
        inputs=[(p,'training') for p in a.treino]+[(p,'testing') for p in a.teste];mode='sessao'
    else:p.error('Use --entrada OU --treino e --teste')
    try:r=export(inputs,a.saida,a.fonte,mode)
    except ValueError as e:p.exit(1,str(e)+'\n')
    print(json.dumps(r['janelas_por_subset_classe'],ensure_ascii=False))
if __name__=='__main__':main()

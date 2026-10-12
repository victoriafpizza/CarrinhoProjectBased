"""Compila o MESMO policy.h do firmware. --compiler caminho/zig.exe."""
import argparse,subprocess,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build(compiler):
    target=ROOT/'simulacao/native';target.mkdir(exist_ok=True)
    dll=target/('policy.dll' if sys.platform=='win32' else 'policy.so')
    cmd=[str(compiler)]
    if Path(compiler).stem.lower()=='cl':
        cmd += ['/nologo','/O2','/GS-','/Zl','/LD',str(ROOT/'simulacao/policy_bridge.cpp'),'/link','/NOENTRY','/NODEFAULTLIB','/OUT:'+str(dll)]
    else:
        if Path(compiler).stem=='zig':cmd+=['c++']
        cmd+=['-std=c++14','-shared','-O2',str(ROOT/'simulacao/policy_bridge.cpp'),'-o',str(dll)]
        if sys.platform!='win32':cmd+=['-fPIC']
    result=subprocess.run(cmd,cwd=target,capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    files=['software/carrinho_tinyml/policy.h','simulacao/policy_bridge.cpp']
    manifest={'compilador':str(compiler),
              'fontes':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
              'biblioteca':dll.name,'sha256':hashlib.sha256(dll.read_bytes()).hexdigest()}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps(manifest,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);a=p.parse_args();build(a.compiler)

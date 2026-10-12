import ctypes,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATES={'DESCONHECIDO':0,'LIVRE':1,'ATENCAO':2,'PERIGO':3}
class NativePolicy:
    def __init__(self):
        target=ROOT/'simulacao/native';manifest=json.loads((target/'manifest.json').read_text(encoding='utf-8'))
        for name,sha in manifest['fontes'].items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise RuntimeError('policy.h mudou: recompile policy_bridge')
        path=target/manifest['biblioteca']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['sha256']:raise RuntimeError('Hash da biblioteca de decisÃ£o diverge')
        self.lib=ctypes.CDLL(str(path))
        self.lib.cp2_gate.argtypes=[ctypes.c_int]*6+[ctypes.POINTER(ctypes.c_int)]
        self.lib.cp2_gate.restype=None
        self.lib.cp2_fresh.argtypes=[ctypes.c_uint32]*3;self.lib.cp2_fresh.restype=ctypes.c_int
    def gate(self,left,right,label,healthy,reverse=True,sign=1):
        if sign not in (-1,1):raise ValueError('Sinal fÃ­sico deve ser +1/-1')
        out=(ctypes.c_int*2)();self.lib.cp2_gate(left,right,STATES.get(label,0),bool(healthy),bool(reverse),sign,out)
        return tuple(out)
    def fresh(self,now,last,timeout):return bool(self.lib.cp2_fresh(now,last,timeout))

#include "../software/carrinho_tinyml/policy.h"
#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif
extern "C" EXPORT void cp2_gate(int left,int right,int state,int healthy,int reverse,int sign,int *out){
    auto d=gate(left,right,static_cast<Proximity>(state),healthy!=0,reverse!=0,sign);
    out[0]=d.left;out[1]=d.right;
}
extern "C" EXPORT int cp2_fresh(CP2Time now,CP2Time last,CP2Time timeout){return fresh(now,last,timeout);}

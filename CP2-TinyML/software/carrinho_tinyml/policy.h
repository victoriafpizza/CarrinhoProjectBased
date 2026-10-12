#pragma once
using CP2Time = unsigned int;
static_assert(sizeof(CP2Time)==4,"CP2 exige relógio de 32 bits");
enum class Proximity { Unknown, Livre, Atencao, Perigo };
struct Drive { int left; int right; };
inline Drive gate(int left,int right,Proximity c,bool healthy,bool reverseAllowed,int forwardSign) {
    if(!healthy || c==Proximity::Unknown)return {0,0};
    if(c==Proximity::Perigo) {
        // Apenas ré com ambas as rodas afastando; sem pivô ou curva com roda avançando.
        if(!reverseAllowed || left*forwardSign>0 || right*forwardSign>0)return {0,0};
        return {left/2,right/2};
    }
    if(c==Proximity::Atencao && (left*forwardSign>0 || right*forwardSign>0))return {left/2,right/2};
    return {left,right};
}
inline bool fresh(CP2Time now,CP2Time last,CP2Time timeout){return CP2Time(now-last)<=timeout;}

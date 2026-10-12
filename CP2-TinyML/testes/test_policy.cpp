// Teste do MESMO policy.h usado no firmware. Executar quando houver compilador C++.
#include "../software/carrinho_tinyml/policy.h"
#include <cassert>
int main(){
 auto d=gate(200,200,Proximity::Livre,true,false,1);assert(d.left==200&&d.right==200);
 d=gate(200,100,Proximity::Atencao,true,false,1);assert(d.left==100&&d.right==50);
 d=gate(200,200,Proximity::Perigo,true,false,1);assert(d.left==0&&d.right==0);
 d=gate(-100,-80,Proximity::Perigo,true,true,1);assert(d.left==-50&&d.right==-40);
 d=gate(100,-100,Proximity::Perigo,true,true,1);assert(d.left==0&&d.right==0);
 d=gate(200,200,Proximity::Livre,false,false,1);assert(d.left==0&&d.right==0);
 d=gate(200,200,Proximity::Unknown,true,false,1);assert(d.left==0&&d.right==0);
 d=gate(-200,-200,Proximity::Atencao,true,false,-1);assert(d.left==-100&&d.right==-100);
 assert(fresh(20,0xfffffff0U,50));assert(!fresh(400,0,350));
}

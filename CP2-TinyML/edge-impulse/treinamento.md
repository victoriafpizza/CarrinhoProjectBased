# Plano de treinamento — não executado

Modelo inicial: uma entrada de 10 distâncias, Raw Data, Dense 16 ReLU,
Dense 8 ReLU, saída 3 classes Softmax. Tente 50 épocas, learning rate 0,001,
batch 8; ajuste somente com treino/validação. São propostas, não parâmetros
confirmados na plataforma. Compare modelos menores antes de aumentar camadas.

O dataset fornecido tem poucas janelas e uma sequência por classe. Uma validação
interna aleatória do Studio pode misturar trechos correlacionados. Registre essa
limitação; Model Testing externo usa somente os seis arquivos reservados.
Dados reais devem usar sessões/cenários independentes em treino, validação e teste.
Não ajuste arquitetura ou confiança repetidamente usando o teste final.

Após Train, registre valores e screenshots reais em resultados.md. Rode Model
Testing > Classify all; preserve matriz de confusão e resultados por amostra.
Examine transições LIVRE→ATENCAO→PERIGO: o dataset atual só contém classes estáveis.

Deployment > Arduino library: escolha otimização/quantização disponível, gere
build, baixe ZIP original para modelo/. Instale por Add .ZIP Library no Arduino
IDE. Copie o nome verdadeiro do *_inferencing.h para config_local.h.
Registre projeto ID/URL, data de exportação, versão, SHA256 ZIP, parâmetros,
constantes de entrada, labels e precisão escolhida (int8/float32).

Confira RAM/ROM/latência no alvo ESP32 selecionado; depois meça no ESP32 físico.
Uma estimativa para outro alvo não é uma medição no carrinho.
Não há biblioteca exportada nesta entrega e run_classifier não foi substituído.

Referência de implementação real:
https://github.com/edgeimpulse/inferencing-sdk-cpp/blob/master/classifier/ei_run_classifier.h

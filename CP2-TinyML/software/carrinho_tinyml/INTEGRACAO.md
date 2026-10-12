# Integração preparada, ainda não compilada

O mapeamento preservado do CP1 é:

| Motor | PWM | IN1 | IN2 |
|---|---:|---:|---:|
| DD | 25 | 26 | 27 |
| DE | 13 | 12 | 14 |
| TD | 15 | 2 | 4 |
| TE | 18 | 19 | 21 |

O broker PicoMQTT fica no ESP32 carrinho, AP `ESP32_Rede_MQTT`; joystick usa
PubSubClient, publica `carrinho/joystick` com JSON x/y inteiros -255..255 a 50 ms.
Mistura preservada: esquerda=y+x, direita=y-x; saturação -255..255.
A senha de AP mantém a configuração já presente no CP1 para compatibilidade.

O original reúne dois programas com setup/loop duplicados, tem `LOW);0` e
termina com `)` em vez de `}`. Nada foi corrigido no original. O carrinho CP2
é um sketch independente; controle_cp2 extrai o PROGRAMA 2 e corrige somente
o fechamento final. O firmware funcional já instalado no joystick pode continuar.

1. Confirme modelo exato da placa ESP32, GPIOs TRIG/ECHO e sentido físico do
   avanço. 22/23 no arquivo antigo são exemplos, não confirmação física.
2. Instale Arduino-ESP32 3.x e registre versão exata; o CP1 usa ledcAttach e
   ledcWrite por pino, APIs da série 3.x. No ambiente inspecionado há AVR, sem
   pacote ESP32 localizado. Instale PicoMQTT e ArduinoJson 7.x; registre versões.
3. Instale biblioteca real exportada pelo Studio; crie config_local.h usando
   config_local.example.h. Defina todos os macros; CP2_ALLOW_REVERSE deve começar 0.
4. Compile carrinho_tinyml.ino para a placa real. Modelo deve ter um eixo,
   10 leituras, intervalo ~150 ms e 3 classes com nomes esperados. Compilação
   deliberadamente bloqueada se faltar confirmação ou modelo.
5. Confira pinout da placa. O teste estático detecta conflitos com motores,
   mas não substitui a conferência elétrica/pinos reservados do módulo.

Janela sem sobreposição; 10 distâncias em cm na ordem cronológica, sem dividir
por 400 nem normalizar novamente. Usa signal_from_buffer e run_classifier.
Confiança mínima proposta 0,80, a calibrar com validação real. Classe desconhecida,
NaN, timeout do sensor, atraso de amostragem ou erro de inferência invalidam estado
e solicitam parada. Reconstruir janela inteira após uma falha.

LIVRE permite joystick; ATENCAO reduz PWM pela metade quando alguma roda avança;
PERIGO para ambos os lados diante de qualquer componente de avanço. Ré só se
explicitamente habilitada, com ambas rodas afastando e potência reduzida.
Sem reversão automática. Nenhuma classe de ação é produzida por limite fixo de cm.
Os limites 2..400 só validam o sensor; 25/60 só rotulam dataset.

Watchdog de comando: 350 ms desde último payload válido, além de estação Wi-Fi.
Predição expira em 1800 ms. Parada durante inferência síncrona evita continuar
um comando antigo enquanto MQTT não é processado. Pulso HC-SR04 pode bloquear
até 30 ms; atrasos maiores de amostragem reiniciam janela. Isso pode provocar
paradas conservadoras se o dispositivo não cumprir o orçamento de tempo.

Limitante: classificação com janela 1500 ms pode reagir tarde a obstáculo súbito;
mistura de classes na transição ainda não foi treinada. Distância de parada depende
da velocidade, atraso, bateria e inércia. Avaliar com rodas suspensas, depois em
baixa velocidade e área livre; medir latência e distância de parada antes do vídeo.
Saída PWM zero/desativação da ponte não garante frenagem instantânea do chassi.

PWM oficial: https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html

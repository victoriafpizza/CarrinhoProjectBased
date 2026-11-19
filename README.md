# ROTA LIVRE — Mobilidade Inteligente e Acessibilidade Urbana

**FIAP · Engenharia de Software · Global Solution 2026.2 — CitizenTech**

**Disciplina** — Project-Based Maker Lab

**Aluna** — Victoria Franceschini Pizza · **RM** 550609

## Resumo executivo

O ROTA LIVRE estuda a percepção de obstáculos e a resposta motora em um percurso controlado. A implementação parte de um carrinho 4WD comandado por joystick via Wi-Fi/MQTT. A evolução incorpora ao código a coleta ultrassônica, um pipeline de dados e uma política de redução ou bloqueio do movimento conforme a proximidade. A preparação de dados e a simulação por regras foram verificadas. A inferência embarcada depende de uma biblioteca de modelo treinado, confirmação dos GPIOs e validação no veículo.

## Problema social e contexto CitizenTech

Obstáculos em áreas de circulação prejudicam a previsibilidade e a acessibilidade dos deslocamentos, especialmente para pessoas com mobilidade reduzida. O recorte do Maker Lab é a detecção de proximidade frontal e a resposta motora de um protótipo em pequena escala. O projeto permite investigar como a distância e a latência de reação afetam a circulação em um ambiente representativo.

## Objetivos gerais e específicos

**Objetivo geral** — Investigar percepção local e respostas contextualizadas em um protótipo robótico voltado à mobilidade acessível.

- Evoluir a base 4WD mantendo a interface de controle remoto.
- Coletar e preparar janelas temporais de distância para classificação.
- Verificar a política de redução e parada em situações de aproximação e falha.
- Preparar a integração embarcada e a medição de resposta física em bancada.

## Visão geral da solução

O carrinho é a unidade experimental de percepção e atuação do ROTA LIVRE. O operador solicita direção e velocidade. O firmware CP2 foi escrito para autorizar, limitar ou bloquear essa solicitação conforme a leitura do sensor, a classificação local e o estado da comunicação. No computador, a simulação exercita esse fluxo com entradas sintéticas. O código do carrinho não integra API, aplicativo, GPS ou câmera.

## Arquitetura do sistema

```text
Joystick X/Y → ADC do ESP32 controle → Wi-Fi / MQTT / JSON
                                           ↓
HC-SR04 → TRIG/ECHO → ESP32 carrinho (AP + broker PicoMQTT)
                           │               │
                  janela de 10 leituras    mistura diferencial
                           ↓               ↓
               Edge Impulse (biblioteca requerida) → policy.h
                                                         ↓
                                            PWM + direção → pontes H
                                                         ↓
                                               quatro motores DC
```

O AP local é `ESP32_Rede_MQTT`. O cliente conecta a `192.168.4.1:1883` e publica no tópico `carrinho/joystick` um JSON como `{"x":0,"y":200}`, com inteiros de −255 a 255 e pausa de 50 ms entre publicações. A serial de diagnóstico opera a 115200 baud. [Controle](CP2-TinyML/software/controle_cp2/controle_cp2.ino) · [Carrinho](CP2-TinyML/software/carrinho_tinyml/carrinho_tinyml.ino)

## Componentes de hardware

| Componente | Quantidade documentada | Papel e confirmação necessária |
|---|---:|---|
| ESP32 | 2 | Uma placa para o joystick e outra para o veículo. Confirmar variante de cada placa. |
| Joystick e shield | 1 conjunto | Entrada analógica X/Y. Confirmar pinagem e alimentação do módulo. |
| HC-SR04 | 1 previsto no CP2 | Distância frontal. O relato CP1 já cita ultrassom após o MVP. O CP2 incorpora a leitura ao firmware. Confirmar módulo e eventual adição física posterior ao CP1. |
| Pontes H | 2 | Comutam os quatro motores. Confirmar modelo, layout de bornes e distribuição de canais entre módulos. |
| Motores DC e chassi 4WD | 4 motores e 1 chassi | Dois motores por lado. Confirmar polaridade e sentido em bancada. |
| Pilhas, montagem e carenagem | 12 pilhas, 2 mini protoboards, cabos e carenagem no relato CP1 | Confirmar tipo e arranjo das pilhas, reguladores, tensões, corrente e proteções. |

O relato histórico descreve a evolução do chassi, da organização elétrica e do encaixe e posição dos vidros da carenagem. As fotos e o diagrama são do protótipo anterior. [README CP1 no Git](https://github.com/victoriafpizza/cpCarrinho/blob/08da745ee9625781aa495e9dc2f7d84b97399af5/readme.md) · [Diagrama](diagramaDeFuncionamento.png) · [Fotos](img/)

## Mapeamento de pinos e conexões

DD/DE são dianteiro direito/esquerdo. TD/TE são traseiro direito/esquerdo. Para os motores, a ordem é **PWM, IN1, IN2**.

| Componente | Função | GPIO/Pino | Evidência no código |
|---|---|---|---|
| Ponte H → motor DD | PWM e direção | 25, 26, 27 | [CP1](main.ino), `PinoPWMDD` e [CP2](CP2-TinyML/software/carrinho_tinyml/carrinho_tinyml.ino), `drive()` |
| Ponte H → motor DE | PWM e direção | 13, 12, 14 | CP1, `PinoPWMDE` e CP2, `drive()` |
| Ponte H → motor TD | PWM e direção | 15, 2, 4 | CP1, `PinoPWMTD` e CP2, `drive()` |
| Ponte H → motor TE | PWM e direção | 18, 19, 21 | CP1, `PinoPWMTE` e CP2, `drive()` |
| Joystick X/Y | Entradas ADC do ESP32 controle | 34 e 35 | [Controle CP2](CP2-TinyML/software/controle_cp2/controle_cp2.ino), `pinX/pinY` |
| HC-SR04 TRIG | Saída digital do ESP32 carrinho | A confirmar. 22 é exemplo histórico. | [Sketch CP2](CP2/coleta_hcsr04.ino), `PIN_TRIG` e [configuração TinyML](CP2-TinyML/coleta/config_coleta.example.h), `CP2_PIN_TRIG` |
| HC-SR04 ECHO | Entrada digital de duração do pulso | A confirmar. 23 é exemplo histórico. | Sketch CP2, `PIN_ECHO` e configuração TinyML, `CP2_PIN_ECHO` |
| HC-SR04 VCC/GND | Alimentação e referência | 5 V para HC-SR04 convencional e GND comum, sujeitos à confirmação da montagem | [Orientação de coleta](CP2/readmeCP2.md) |
| Interface serial | Diagnóstico e coleta no computador | Interface da placa, sem GPIO declarado nos sketches | `Serial.begin(115200)` |

Conectar os GPIOs de comando às entradas lógicas da ponte H e os motores às saídas de potência. Confirmar terras comuns e GPIOs reservados. Em um HC-SR04 convencional, adaptar o ECHO de 5 V à entrada de 3,3 V do ESP32 antes de energizar. O firmware verifica conflito dos GPIOs de TRIG/ECHO com os dos motores em compilação. [Integração](CP2-TinyML/software/carrinho_tinyml/INTEGRACAO.md)

## Tecnologias e bibliotecas

| Ambiente | Recursos | Uso |
|---|---|---|
| Arduino IDE / C++ | Arduino-ESP32 3.x, `WiFi.h` e LEDC | AP/estação, GPIO, ADC, PWM. Revisão exata do core e modelo da placa pendentes. |
| ESP32 veículo | PicoMQTT e ArduinoJson 7.x | Broker local e validação do JSON. |
| ESP32 controle | PubSubClient e ArduinoJson | Cliente MQTT e serialização do joystick. |
| ESP32 TinyML | Biblioteca Arduino exportada do Edge Impulse | Metadados, `signal_from_buffer` e `run_classifier`. Exportação ausente. |
| Coleta no computador | Python 3 e `pyserial==3.5` | Leitura serial e CSV. |
| Simulação | Python 3.10+, `ctypes`, C++ e Tkinter para interface gráfica | Reuso de `policy.h` com biblioteca nativa. O modo B exige também NumPy e ONNX Runtime. |

O repositório usa sketches Arduino e não inclui configuração PlatformIO nem versões exatas das bibliotecas Arduino. [Dependências Python](CP2-TinyML/coleta/requirements.txt) · [Manifesto da DLL Windows](CP2-TinyML/simulacao/native/manifest.json)

## Inteligência artificial e integração com sensores

O plano no Edge Impulse especifica uma série de um eixo (`distancia_cm`) a aproximadamente 6,67 Hz, entrada Raw Data, janela e incremento de 1.500 ms e rede densa 16 → 8 → 3, com 50 épocas e taxa de aprendizado 0,001. São parâmetros propostos. Não há link público do projeto, relatório de treinamento, métricas, biblioteca Arduino ou modelo ONNX no repositório. [Configuração](CP2-TinyML/edge-impulse/configuracao.md) · [Treinamento](CP2-TinyML/edge-impulse/treinamento.md) · [Resultados](CP2-TinyML/edge-impulse/resultados.md) · [Modelo](CP2-TinyML/modelo/README.md)

O TRIG envia um pulso de 10 µs. A duração de ECHO é convertida por `distancia_cm = duracao_us * 0.0343 / 2`, com timeout de 30 ms e faixa válida de 2 a 400 cm. Dez leituras em centímetros entram em ordem temporal, uma a cada 150 ms, sem normalização manual. As posições vão de 0 a 1.350 ms dentro da janela nominal de 1.500 ms. Os CSVs brutos em CP2 e CP2-TinyML têm SHA-256 idêntico e são tratados como sintéticos. O manifesto registra 450 leituras, 150 por classe, 36 janelas de treino, seis de teste e 30 leituras descartadas entre os conjuntos. As janelas não atravessam classes nem compartilham leituras. [Preparador](CP2-TinyML/coleta/preparar_dataset.py) · [Manifesto dos dados](CP2-TinyML/dataset/validacao.json)

| Classe | Limite de referência para rotulagem e simulação A | Ação da política com sistema saudável |
|---|---|---|
| `LIVRE` | Acima de 60 cm | Repassa a demanda diferencial. |
| `ATENCAO` | De 25 a 60 cm | Reduz à metade ambos os comandos se algum lado avança. |
| `PERIGO` | Abaixo de 25 cm | Zera ambos os lados por padrão. Com ré habilitada, permite apenas comandos sem componente de avanço, à metade da potência. |

No firmware, `infer()` para os motores, encapsula a janela e chama `run_classifier` de forma síncrona. A maior saída precisa ser pelo menos 0,80. Valores inválidos e rótulos desconhecidos impedem movimento. A classificação prevista vem do modelo, enquanto a associação entre classe e PWM é escrita em C++. A simulação A aplica os limiares diretamente à última leitura válida e não gera probabilidades. O modo B exige ONNX real, manifesto, hash e metadados compatíveis. Sem modelo ele fica indisponível, sem troca automática para regras. [Política](CP2-TinyML/software/carrinho_tinyml/policy.h) · [Adaptadores](CP2-TinyML/simulacao/inference.py)


## Funcionamento detalhado do firmware

1. **Inicialização do carrinho.** `setup()` configura direção, PWM de 5 kHz/8 bits, TRIG/ECHO e serial. Valida o período do modelo, 150 ms com tolerância de 1 ms, inicia o AP e configura a inscrição MQTT. Falha na configuração PWM/AP ou intervalo incompatível bloqueiam movimento.
2. **Joystick.** `setupWiFi()` associa o controle ao AP e `reconnectMQTT()` tenta recuperar a sessão. O laço mapeia cada ADC de 0 a 4095 para −255 a 255 e zera magnitudes menores que 20. Publica e registra o JSON enviado.
3. **Recepção e mistura.** O callback valida JSON, tipo inteiro e faixa. `apply()` calcula esquerda = `y+x` e direita = `y-x`, saturadas separadamente. `drive()` replica o comando em cada par de rodas. O sinal escolhe IN1/IN2 e a magnitude define PWM.
4. **Amostragem.** O `loop()` atende o broker, aplica a política e coleta conforme agenda. Atrasos acima de 15 ms ou leitura inválida chamam `invalidate()`, zeram a saída e exigem nova janela. Ao completar dez amostras, `infer()` atualiza a classe e pode imprimir `TinyML,<classe>,<confiança>,<tempo>_us`.
5. **Falhas e temporização.** A autorização exige uma estação associada, PWM configurado, comando válido de até 350 ms e predição válida de até 1.800 ms. Payload inválido, perda de comunicação, timeout de sensor, falha de inferência e baixa confiança levam à parada. PWM zero indica uma ordem elétrica. A distância de parada depende da montagem e da inércia.

O sketch isolado de coleta aceita `1/2/3` para escolher classe e pausar, `s` para iniciar e `p/q` para pausar. Envia linhas `tempo_ms,distancia_cm,classe` e mensagens `# INVALID` de diagnóstico. O capturador preserva a classe manual, rejeita registros inconsistentes e grava CSV com metadados por sessão. [Sketch de coleta](CP2-TinyML/coleta/coleta_hcsr04.ino) · [Capturador](CP2-TinyML/coleta/sensor.py)

## Histórico de Desenvolvimento e Versionamento

Foram examinados os **11 commits** alcançáveis. As referências locais `main`, `origin/main` e `origin/HEAD → origin/main` apontavam para `08da745`. Não havia tags. As datas abaixo são de autoria. O `main.ino` ficou idêntico entre o primeiro commit e o HEAD auditado.

| Versão/Commit | Data | Alteração principal | Impacto técnico |
|---|---|---|---|
| `1947e28` | 16/09/2026 | Adiciona código e README inicial | Base versionada com controle MQTT, mistura diferencial e dois programas ESP32 em um arquivo. O relato documenta a montagem 4WD. |
| `042e157` | 16/09/2026 | Adiciona quatro fotografias | Registra o protótipo. |
| `be1ffe4` | 16/09/2026 | Move fotos para `img/` e adiciona diagrama | Organiza a evidência visual. |
| `b0f586e` | 17/09/2026 | Atualiza README histórico em linha paralela | Revisão exclusivamente documental. |
| `3cf3d7d` | 12/10/2026 | Prepara coleta HC-SR04 e ferramentas para CSV | Aquisição isolada, confirmação de GPIOs, gerador sintético e rótulos por sessão. |
| `5767594` | 12/10/2026 | Versiona dataset sintético e janelas | Separa leitura de treino e teste, com purga e manifesto. |
| `b1916fe` | 12/10/2026 | Documenta plano do Edge Impulse | Especifica entrada, treinamento, testes e exportação pendentes. |
| `e5715b7` | 12/10/2026 | Introduz sketches separados e política embarcada | Corrige fechamento do controle extraído, conserva pinagem e mistura, acrescenta coleta, inferência, watchdog e parada. |
| `e18ec23` | 12/10/2026 | Registra testes, hashes e roteiro físico | Preserva a evidência de dados e identifica os ensaios pendentes. |
| `905c317` | 12/10/2026 | Adiciona `CP2/`, simulador, adaptadores, DLL e trilha | Reutiliza a política C++ no computador e explicita o relógio de 32 bits. |
| `08da745` | 12/10/2026 | Integra as linhas por merge | Estado de código auditado, com o CP2 e a documentação histórica reunidos. |

O relato do CP1 usa `v0.1` a `v1.0` para descrever proposta, chassi, motores, controle, organização eletrônica, ultrassom, alimentação, carenagem, integração e apresentação. O CP2-TinyML usa `v0.1` para a etapa de dados sintéticos e preparação da integração. São rótulos documentais. A comparação de código se baseia nos commits e arquivos preservados. [README histórico do CP1](https://github.com/victoriafpizza/cpCarrinho/blob/08da745ee9625781aa495e9dc2f7d84b97399af5/readme.md) · [README CP2-TinyML](CP2-TinyML/README.md)

| Firmware | Diferença verificável |
|---|---|
| [`main.ino`](main.ino) | Referência CP1. Dois pares de `setup()/loop()`, erro `LOW);0` e fechamento final incorreto. Sem rotina de leitura ultrassônica. |
| [`CP2/coleta_hcsr04.ino`](CP2/coleta_hcsr04.ino) | Coleta separada com pinos exemplificativos. O código troca classe sem pausar, embora o roteiro histórico indique pausa. |
| [`CP2-TinyML/coleta/coleta_hcsr04.ino`](CP2-TinyML/coleta/coleta_hcsr04.ino) | Exige configuração dos pinos, pausa ao trocar a classe e registra erros de temporização e sensor. |
| [`controle_cp2.ino`](CP2-TinyML/software/controle_cp2/controle_cp2.ino) | Extrai o programa do controle, corrige o fechamento e mantém pinagem, mensagens e broker esperado. |
| [`carrinho_tinyml.ino`](CP2-TinyML/software/carrinho_tinyml/carrinho_tinyml.ino) | Evolução atual do veículo em código. Integra leitura e política de inferência à mesma pinagem de motores. Gravação e execução física pendentes. |

**Pasta adjacente auditada.** `C:\Teste\GlobalSolution` não tem histórico Git acessível. Contém 16 variantes de visão para uma bolinha e o peso `best.pt`. `mach1.py`, `mach2.py` e `mach6.py` carregam esse peso com Ultralytics YOLO, com inferência em região de interesse em `mach6.py`. As demais variantes exploram movimento com OpenCV, trajetória, Kalman, velocidade, altura ou gravação. Comentários registram dificuldade para detectar a bolinha em movimento e indicam que a tentativa de melhorar FPS em `mach14.py` foi preterida. A versão final não é identificável pelo nome. Não há comunicação ou fluxo de dados comprovado entre esses scripts e o carrinho, nem métricas ou registro de treinamento do peso.

## Estrutura de arquivos do repositório

| Caminho | Conteúdo |
|---|---|
| [`main.ino`](main.ino), [`img/`](img/) e [diagrama](diagramaDeFuncionamento.png) | Firmware histórico e evidências visuais do CP1. |
| [`CP2/`](CP2/) | Sketch de coleta, `capturar_serial.py`, `sensor.py`, CSV e roteiro histórico. |
| [`CP2-TinyML/coleta/`](CP2-TinyML/coleta/) | Sketch, configuração, capturador, gerador sintético, preparador e requisitos. |
| [`CP2-TinyML/dataset/`](CP2-TinyML/dataset/) | CSV, manifestos e janelas em treino, teste e preparado_simulado. `dados_reais/` contém marcador. |
| [`CP2-TinyML/edge-impulse/`](CP2-TinyML/edge-impulse/) e [`modelo/`](CP2-TinyML/modelo/) | Plano de treinamento e área reservada à exportação. |
| [`CP2-TinyML/software/`](CP2-TinyML/software/) | Sketches separados, configuração, integração e política. |
| [`CP2-TinyML/simulacao/`](CP2-TinyML/simulacao/) | Cenários, CLI/GUI, inferência e ponte C++ com DLL e manifesto. |
| [`CP2-TinyML/testes/`](CP2-TinyML/testes/) e [`evidencias/`](CP2-TinyML/evidencias/) | Testes, trilha, hashes, logs e roteiro físico. |
| [`CP2-TinyML/commits.ps1`](CP2-TinyML/commits.ps1) | Script histórico de montagem dos commits, dispensável para instalação. |

## Pré-requisitos e instalação

- **Simulação.** Usar Python 3.10 ou superior. Windows, Python 3.12.14 e a DLL versionada foram usados na auditoria. Em outras plataformas, gerar a biblioteca com `simulacao/build_policy.py --compiler CAMINHO_DO_COMPILADOR` em uma cópia de trabalho. Tkinter é necessário para a interface gráfica.
- **Coleta.** Instalar `python -m pip install -r coleta/requirements.txt` em `CP2-TinyML` e ter uma porta serial disponível.
- **Bancada.** Usar os dois ESP32 e conferir joystick, HC-SR04, adaptação de ECHO, pontes H, motores e alimentação. Instalar Arduino IDE, core Arduino-ESP32 3.x e bibliotecas da tabela. Selecionar placa e porta reais.
- **TinyML.** Coletar sessões independentes, preparar treino/teste, treinar e validar no Edge Impulse. Importar o ZIP Arduino exportado e registrar versões, header, hash e métricas. Para o modo B também é necessário o ONNX e `modelo/desktop/model.json` compatíveis com o carregador.

## Como compilar e executar

**Computador.** Executar a partir da raiz do repositório. Escolher nomes inéditos para as saídas. Para abrir a GUI, omitir `--headless` e usar Tkinter.

```powershell
Set-Location CP2-TinyML
python -m unittest discover -s testes -v
python simulacao/simulador_carrinho.py --headless --mode A --cenario LIVRE --saida livre_local.json
python coleta/preparar_dataset.py --entrada dataset/dados_simulados_cp2.csv --fonte simulado --saida dataset/nova_preparacao
```

A trilha contém tempo, distância, classe, motivo, comandos, PWM por motor e posição simulada. No modo A, confiança aparece como `null` e não há probabilidades de modelo.

**Arduino IDE — procedimento de bancada ainda não validado nesta auditoria.**

1. Para coletar, copiar o sketch de `CP2-TinyML/coleta/` para uma pasta de sketch `coleta_hcsr04`. Copiar o exemplo de configuração como `config_coleta.h` ao lado do sketch e definir TRIG, ECHO e confirmação após conferir a montagem. Usar **Verificar** e **Carregar** para gravar na placa do veículo com as rodas paradas.
2. Fechar o Monitor Serial. Em `CP2-TinyML`, capturar com o comando abaixo, substituindo `COM5`. Repetir em arquivos separados para `ATENCAO` e `PERIGO`, documentando cenários. Preparar sessões completas com a opção `--fonte real --treino ... --teste ...` do preparador.
3. Após importar a biblioteca Arduino real, copiar `config_local.example.h` para `config_local.h` junto ao firmware do veículo. Definir `CP2_PIN_TRIG`, `CP2_PIN_ECHO`, `CP2_PINS_CONFIRMED`, `CP2_EI_HEADER` e `CP2_FORWARD_SIGN` de acordo com montagem, exportação e sentido físico. Manter `CP2_ALLOW_REVERSE=0` inicialmente.
4. Abrir `carrinho_tinyml.ino` e `controle_cp2.ino` separadamente. Selecionar cada placa e porta, verificar e gravar. Registrar placa, versões e saídas de compilação e gravação.
5. Com rodas suspensas, verificar partida parada, neutralidade do joystick, direção, Wi-Fi/MQTT e logs a 115200 baud. Exercitar perda de conexão e sensor inválido. Medir latência e distância de parada a baixa velocidade em ambiente controlado antes da apresentação.

```powershell
python coleta/sensor.py --porta COM5 --classe LIVRE --segundos 30 --cenario objeto_plano_sessao1 --saida dataset/dados_reais/livre_sessao1.csv
```

[Integração](CP2-TinyML/software/carrinho_tinyml/INTEGRACAO.md) · [Roteiro físico](CP2-TinyML/testes/roteiro_fisico.md)


## Testes e Validação

| Teste | Objetivo | Resultado observado | Evidência |
|---|---|---|---|
| Dataset sintético | Validar formato, limites, rótulos, lacunas e separação | 14 testes Python passaram, em concordância com o log histórico. Os CSVs brutos têm SHA-256 idêntico. | [Testes](CP2-TinyML/testes/test_dataset.py) · [Log](CP2-TinyML/evidencias/testes_python.txt) |
| Partida e condição livre | Aguardar janela e liberar avanço por regra | Na trilha versionada, a primeira classe LIVRE surge em 1.500 ms e o PWM simulado dos quatro motores passa a 200. Aos 6 s, o contador registra zero colisões simuladas. | [Trilha](CP2-TinyML/evidencias/simulacao/livre_A.json) |
| Obstáculos e transições | Exercitar LIVRE, ATENCAO e PERIGO | Os cenários isolados retornaram 200, 100 e 0 por lado para demanda 200. A aproximação percorreu as três classes em modo A. | [Suíte de simulação](CP2-TinyML/testes/test_simulacao.py) |
| Falhas, JSON e atuadores | Verificar mensagem inválida, desconexão, timeout, sensor inválido, baixa confiança, ré e mistura | 26 testes de simulação/ponte nativa passaram. A baixa confiança foi injetada. JSON e motores foram simulados. | [Casos de teste](CP2-TinyML/testes/test_simulacao.py) · [Política](CP2-TinyML/software/carrinho_tinyml/policy.h) |
| Teste C++ independente | Executar asserções de `policy.h` fora do simulador | A tentativa com MSVC chegou à vinculação e encontrou `LNK1104` para `kernel32.lib`. Resultado desse executável não comprovado. A política foi exercitada via DLL na suíte Python. | [Teste C++](CP2-TinyML/testes/test_policy.cpp) |
| Modelo real em computador e ESP32 | Verificar classes, probabilidades e inferência | Não comprovado. A suíte registrou 40 testes executados e uma classe de testes ignorada por ausência de ONNX Runtime. O modelo também está ausente do repositório. | [Testes do modo B](CP2-TinyML/testes/test_simulacao.py) · [Área do modelo](CP2-TinyML/modelo/README.md) |
| Sensor físico, MQTT, motores e parada | Demonstrar o conjunto e medir distância de parada | Não comprovado no CP2. Fotos e relato histórico registram o CP1. O roteiro físico ainda depende de execução documentada. | [Fotos](img/) · [Roteiro](CP2-TinyML/testes/roteiro_fisico.md) · [Status](CP2-TinyML/evidencias/STATUS.md) |

Também foram reexecutados o simulador em modo A e o preparador de dados, com saída temporária. A CLI reproduziu o cenário LIVRE em 6 s com PWM 200 por motor e zero colisões simuladas, e o preparador gerou 36 janelas de treino e seis de teste. A suíte Python emitiu um `ResourceWarning` sobre um CSV aberto pelo simulador e terminou com sucesso. Compilação e upload no ESP32 não foram validados. A instalação Arduino inspecionada não continha o pacote ESP32.

## Limitações conhecidas

- O ultrassom amostra a região frontal. Superfície, ângulo, temperatura e vibração podem afetar a medição.
- A janela nominal de 1,5 s, o timeout de até 30 ms da leitura e a inferência síncrona podem retardar a reação. A distância de parada precisa ser medida fisicamente.
- O dataset tem uma sequência sintética contínua por classe. A separação temporal reduz compartilhamento direto de amostras, mas não demonstra generalização para transições ou cenários independentes.
- O operador fornece a trajetória. A autonomia prevista é supervisória e atua na redução ou no bloqueio do movimento. O código não planeja rotas nem executa desvios automáticos.
- As credenciais Wi-Fi estão fixas no código e não há autenticação MQTT configurada no broker.

## Melhorias futuras

1. Conferir a montagem, a alimentação, os níveis elétricos e a evolução física do sensor.
2. Coletar sessões independentes e transições, validar o classificador e conservar exportação, versões e métricas.
3. Gravar os sketches nas placas identificadas e medir latência, falsos alarmes e distância de parada em testes controlados.
4. Registrar funcionamento, acabamento, segurança e resposta a falhas no vídeo acadêmico.

## Vídeo demonstrativo

**Pendente.** Os arquivos auditados não contêm vídeo ou link demonstrativo do ROTA LIVRE. O enunciado pede até seis minutos. O registro deve apresentar a identificação acadêmica, a montagem e o funcionamento físico, incluindo o sensor, as respostas contextuais e o comportamento diante de falhas. [Roteiro físico](CP2-TinyML/testes/roteiro_fisico.md)

## Conclusão técnica

O histórico comprova a evolução do controle diferencial para uma arquitetura que prevê ultrassom, classificação local e política de atuação. Testes de dados e de simulação demonstram o comportamento da política sob entradas sintéticas. Para demonstrar a integração embarcada, ainda é preciso confirmar a montagem, validar o modelo real e testar as duas placas e os motores em conjunto.

## Referências

- [Repositório cpCarrinho](https://github.com/victoriafpizza/cpCarrinho)
- [Documentação CP2-TinyML](CP2-TinyML/README.md)
- [Espressif — API LEDC do Arduino-ESP32](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html)
- [Edge Impulse — importação de dados CSV](https://www.edgeimpulse.com/blog/import-your-data-as-csv/)
- [Edge Impulse — SDK C++ e rotina de classificação](https://github.com/edgeimpulse/inferencing-sdk-cpp/blob/master/classifier/ei_run_classifier.h)

### Conformidade com os critérios da FIAP

A matriz segue o enunciado fornecido. A consulta pública não localizou uma rubrica oficial específica da disciplina para confirmação independente.

| Requisito FIAP | Status | Evidência encontrada | Pendência |
|---|---|---|---|
| Evolução do robô anterior | Comprovado | Código original, commits e módulos CP2. | Demonstrar a revisão atual em bancada. |
| Incorporação de pelo menos um sensor adicional | Parcialmente comprovado | HC-SR04 incorporado ao código em relação ao CP1. O relato do CP1 já menciona ultrassom após o MVP. | Verificar se houve adição física de um sensor além dos usados no CP1 e confirmar GPIOs. |
| Integração de dados sensoriais à IA | Parcialmente comprovado | Coleta, janela e chamada `run_classifier`. | Treinar, exportar e executar o modelo real com o sensor. |
| Respostas contextualizadas | Parcialmente comprovado | Redução, parada e recuperação verificadas em simulação. | Demonstrar respostas no veículo. |
| Autonomia e tomada de decisão | Parcialmente comprovado | Decisão supervisória testada por regras. | Verificar em bancada com inferência embarcada. |
| Integração entre hardware e software | Parcialmente comprovado | Montagem histórica, GPIOs e código dos dois ESP32. | Testar ligação atual, MQTT, atuação e sensor juntos. |
| Adequação ao tema CitizenTech | Comprovado | Escopo acadêmico liga percepção de obstáculos à mobilidade acessível. | Avaliar em cenários representativos de circulação. |
| Testes práticos | Não comprovado | Roteiro físico e relato histórico, com execução de dados e simulação. | Registrar ensaios físicos atuais e resultados. |
| Acabamento e segurança | Parcialmente comprovado | Fotos históricas, carenagem relatada e regras de parada. | Inspecionar montagem atual, alimentação, adaptação do ECHO e parada física. |
| Repositório com código-fonte e documentação | Comprovado | Git com firmware, dados, simulação, testes e documentação. | Anexar artefatos após treinamento e exportação. |
| Instruções de reprodução | Parcialmente comprovado | Suíte de computador reexecutada e instruções de bancada descritas. | Validar compilação, upload e reprodução física ponta a ponta. |
| Identificação dos integrantes | Comprovado | Victoria Franceschini Pizza, RM 550609, no enunciado e na documentação CP2. | — |
| Vídeo demonstrativo de até seis minutos | Não comprovado | Nenhum vídeo ou link localizado. | Gravar e vincular o vídeo de até seis minutos. |

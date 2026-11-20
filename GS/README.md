# ROTA LIVRE — Firmware da Global Solution CitizenTech 2026.2

**FIAP · Engenharia de Software — 4ES · Project-Based Maker Lab**

**Victoria Franceschini Pizza · RM 550609**

O ROTA LIVRE é um carrinho ESP32 com controle Xbox e adaptação automática à luminosidade. O [sketch da GS](firmware/main/main.ino) recebe o comando, aplica um limite de PWM nos dois canais de tração e acende o LED em pouca luz. O [`main.ino` da raiz](../main.ino) continua sendo o firmware histórico do CP1. O [sketch de aquisição](firmware/ldr_monitor/ldr_monitor.ino) conserva o experimento de LDR por serial.

**Estado da verificação.** A sintaxe e os cenários de controle foram exercitados em Windows com APIs simuladas. Nenhum binário ESP32 foi gerado nem houve upload ou validação física da revisão.

## Ligações da GS

| Sinal | GPIO | Uso |
|---|---:|---|
| ENA | 19 | PWM do lado esquerdo |
| IN1 / IN2 | 18 / 5 | Direção do lado esquerdo |
| IN3 / IN4 | 4 / 21 | Direção do lado direito |
| ENB | 15 | PWM do lado direito |
| LDR | 36 | ADC1 no ESP32 clássico |
| LED | 22 | Saída ativa em nível alto, assumida nesta implementação |

A pinagem segue a informação da revisão final. O CarrinhoLuz histórico usava GPIO2 em IN4 e GPIO39 no sensor analógico. O sketch experimental da GS usa GPIO34. O sentido lógico dos dois canais segue a referência CarrinhoLuz: comando positivo ativa a primeira entrada do canal e comando negativo ativa a segunda. O modelo da ponte H, a polaridade montada do LED e o sentido físico dos motores ainda precisam ser verificados. Mantenha terra comum, use resistor em série com o LED e confirme a faixa de tensão do divisor do LDR antes de energizar. GPIO36 é entrada no ESP32 clássico. [Espressif — ADC](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/adc.html)

## Xbox, luminosidade e atuação

O firmware usa `Bluepad32.h` com callbacks de conexão e desconexão. A cada iteração, `BP32.update()` atualiza o estado e `hasData()` indica a chegada de um relatório de entrada. O primeiro controle aceito é a única fonte de tração até desconectar. A tração exige gamepad conectado e relatório recente. A inicialização mantém os pareamentos salvos.

| Botão | Esquerda | Direita | Movimento |
|---|---:|---:|---|
| Y | + | + | Frente |
| A | − | − | Ré |
| B | + | − | Direita |
| X | − | + | Esquerda |
| Nenhum ou dois ou mais botões de movimento | 0 | 0 | Parada |

Já no `setup()`, o firmware configura a direção em nível baixo, inicializa ambos os canais PWM com duty zero e faz a leitura inicial do LDR antes de configurar Bluepad32. No laço, a média inteira de oito leituras de ADC de 12 bits é atualizada nominalmente a cada 25 ms, sem `delay()`. O nível do LED representa o estado escolhido. O PWM a 5 kHz e 8 bits é recalculado para o comando ativo, inclusive se o operador continuar segurando o botão.

| Estado ou leitura | LED | Limite de PWM por canal |
|---|---|---:|
| Valor ajustado abaixo de 1200 | Aceso · ESCURO | 210 |
| Valor ajustado acima de 1600 | Apagado · CLARO | 255 |
| De 1200 a 1600, inclusive | Conserva o estado anterior | Conserva 210 ou 255 |
| Partida na faixa intermediária ou leitura inválida | Aceso · ESCURO conservador | 210 |

Com `SENSOR_INVERTIDO=false`, a comparação usa o ADC bruto. Se o divisor produzir valores maiores quando escurece, confirme em bancada e ajuste a constante para `true`. Nesse modo a comparação usa `4095 − ADC`. Os limiares 1200 e 1600 são valores iniciais do projeto. O código rejeita valores fora de 0–4095 e trata médias nos extremos 0 e 4095 como suspeitas. Uma entrada desconectada pode produzir um valor intermediário plausível, de modo que este teste não detecta toda desconexão. A leitura não é medida em lux, e o duty PWM não é uma medida da velocidade física.

**Proteções de tração.** Sem comando, com botões de movimento conflitantes ou após desconexão, os dois canais ficam zerados. Um intervalo breve sem relatório mantém o último comando por até `TIMEOUT_CONTROLE_MS = 400`. Ao expirar, o comando é descartado. A reconexão exige novos dados antes de mover. Na troca de sentido, o firmware zera o PWM antes de alterar as duas entradas. Erro detectável de configuração ou escrita do PWM bloqueia a tração até reiniciar. A luminosidade altera o teto de PWM, sem gerar um comando de direção. Confirme com as rodas suspensas e mantenha acesso ao corte da alimentação de potência.

**Monitor Serial a 115200 baud.** O log registra conexão, desconexão, timeout, ADC bruto e ajustado, estado, teto PWM e LED. O estado luminoso é registrado na partida, nas mudanças relevantes e, em regime estável, a cada segundo. O teto no log continua sendo 255 ou 210 mesmo quando a saída efetiva está zerada por falta de comando.

## Compilação e teste físico

1. Abra [`firmware/main/main.ino`](firmware/main/main.ino) na Arduino IDE. A pasta `main` corresponde ao nome do sketch.
2. Instale uma combinação de placa ESP32 e Bluepad32 conforme as [instruções oficiais do Bluepad32 para Arduino](https://bluepad32.readthedocs.io/en/latest/plat_arduino/). Selecione o **ESP32 clássico** correspondente à placa e a porta real. Confira se a revisão da biblioteca oferece `ControllerPtr`, `BP32.update()`, `hasData()` e os acessores de botões.
3. O código inclui `Arduino.h`, `Bluepad32.h` e `esp_arduino_version.h`. O ramo Core 2.x usa `ledcSetup`, `ledcAttachPin` e escrita pelo canal. O ramo 3.x usa `ledcAttach` e escrita pelo pino. A combinação real de Core e Bluepad32 deve ser anotada após compilar. [Espressif — migração LEDC do Core 2.x para 3.x](https://docs.espressif.com/projects/arduino-esp32/en/latest/migration_guides/2.x_to_3.0.html)
4. Com a potência da tração isolada, compile, carregue e observe a leitura inicial em claro e escuro. Pareie um gamepad Xbox compatível conforme a documentação dele. Use um controle por vez. Se precisar refazer o pareamento, coloque o controle em modo de pareamento e repita a conexão. O sketch não apaga chaves no boot.
5. Com rodas suspensas, confira os sentidos de Y/A/B/X, solte os botões e repita com pouca luz. Mantenha Y pressionado enquanto varia a luz para verificar a alteração imediata do limite na próxima leitura. Teste desconexão e reconexão antes de usar no chão. Registre se um botão mantido envia relatórios com frequência suficiente para o timeout.

| Verificação | Resultado em Windows, com APIs simuladas | Estado no ESP32 |
|---|---|---|
| Compilação C++ dos ramos 2.x e 3.x | Passou em MSVC 14.44, com avisos tratados como erros | Pendente. Arduino CLI 1.2.0 localizado, com core AVR 1.8.8 e sem core ESP32 ou Bluepad32 encontrados. |
| Partida em claro, escuro e faixa intermediária | LED e limite corresponderam ao estado. Motores iniciaram zerados. | Pendente |
| Histerese, limites exatos e botão mantido | Conservou o estado em 1200–1600 e alternou 255/210 sem novo botão | Pendente |
| Quatro direções e comandos conflitantes | Sinais esperados nos dois canais. PWM zerado antes da inversão e na ausência de comando. | Pendente |
| Timeout, desconexão, reconexão e virada de `millis()` | Casos passaram, inclusive a parada na marca de 400 ms | Pendente |
| Leitura inválida, saturação e erro PWM | Limite reduzido em falha ADC e tração bloqueada nas falhas PWM detectáveis | Pendente |

## Visão computacional e histórico

A automação de luminosidade é uma regra de firmware. O detector YOLO continua no computador, com Python, OpenCV e Ultralytics, e não envia decisões aos motores. O [README principal](../README.md) conserva a auditoria da câmera e dos pesos de visão. O [PDF anterior](documentacao/ROTA-LIVRE-Maker-Lab.pdf) e o [roteiro anterior](documentacao/roteiro-video.md) documentam o experimento de centroides e permanecem como referência histórica. O vídeo final da versão Xbox/LDR/LED ainda precisa ser vinculado.

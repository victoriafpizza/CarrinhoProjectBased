# ROTA LIVRE — Entrega Global Solution CitizenTech 2026.2

**FIAP · Engenharia de Software — 4ES · Project-Based Maker Lab**

**Victoria Franceschini Pizza · RM 550609**

A entrega é **ROTA LIVRE — Robô Inteligente para Monitoramento Ambiental e Identificação de Objetos**. A configuração final foi descrita pela aluna como um carrinho controlado por Xbox, com LDR, LED e redução automática da velocidade em pouca luz. Um celular junto ao carrinho fornece vídeo ao computador por Iriun Webcam. O ESP32 responde às condições de luz e aos comandos do operador. OpenCV e Ultralytics processam o vídeo no computador e exibem as detecções.

A regra de luminosidade é automação local. A IA atua na interpretação dos quadros. As fontes de visão auditadas não transmitem suas decisões ao ESP32. O [README principal](../README.md) reúne a arquitetura, os GPIOs identificados em cada revisão, o tutorial Windows, os testes e a matriz FIAP.

## Evidências e pontos a confirmar

| Componente | O que foi verificado | O que precisa ser confirmado |
|---|---|---|
| Controle Xbox e tração | O ZIP histórico CarrinhoLuz em Downloads contém Bluepad32, PWM e tratamento de perda de comunicação. O CP1 versionado usa joystick e Wi-Fi/MQTT. | Sketch efetivamente gravado, placa, pareamento, comandos, pinagem e ponte H da versão final. |
| Resposta à luz | O [sketch experimental](firmware/ldr_monitor/ldr_monitor.ino) lê GPIO34 e transmite pela serial. O CarrinhoLuz histórico usa sensor analógico no GPIO39 e redução baseada em TinyML. | Identidade do sensor do CP anterior, fiação do LDR e do LED final, limiar, redução, retorno à normalidade e registro de bancada. |
| Webcam do celular | O instalador local identifica **Iriun Webcam**. Os scripts abrem a câmera por índice. | Índice do dispositivo e vídeo da câmera fixada junto ao carrinho em execução. |
| Reconhecimento de objetos | [`best.pt`](../GlobalSolution/best.pt) é YOLOv8n com uma classe verificada, `bolinha de papel`, usado por [`mach2.py`](../GlobalSolution/mach2.py) e variantes. | Arquivo e metadados do peso generalista informado. As 80 classes não estão comprovadas para a entrega. |
| Vídeo | A duração limite da rubrica é de seis minutos. | Inserir o link da versão final e demonstrar iluminação, tração e visão. |

## Reprodução e entrega

1. Siga a [instalação do ESP32, Iriun e Python](../README.md#instalação-e-execução). Para a tração, confira a origem do sketch antes de gravar.
2. Grave o carrinho sob o mesmo comando em condição clara e escura. Mostre o LED, o comportamento das rodas e o retorno à condição inicial.
3. Enquadre a câmera do celular, a cena e a janela Python. Mostre detecções do peso efetivamente carregado e anote as classes.
4. Registre os resultados na [tabela de validação](../README.md#testes-e-validação) e inclua o link em [Vídeo demonstrativo](../README.md#vídeo-demonstrativo).

## Artefatos preservados da proposta anterior

O [PDF ROTA-LIVRE-Maker-Lab.pdf](documentacao/ROTA-LIVRE-Maker-Lab.pdf) e o [roteiro anterior](documentacao/roteiro-video.md) descrevem o protótipo de luminosidade com classificação por centroides. São registros históricos e estão desatualizados para a versão Xbox/LDR/LED/YOLO. Os [dados](dados/), o [modelo experimental](inteligencia-artificial/), a [simulação](simulacao/) e os [resultados sintéticos](evidencias/) desse protótipo foram mantidos para rastreabilidade.

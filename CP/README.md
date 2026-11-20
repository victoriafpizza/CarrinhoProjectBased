# Checkpoints — histórico do carrinho

Os caminhos originais foram mantidos para preservar referências, a conferência dos hashes e a reprodução dos testes. Esta pasta organiza o acesso às etapas sem duplicar fontes ou introduzir dependências para a GS.

| Etapa | Código e evidências | Escopo |
|---|---|---|
| CP1 | [Firmware original](../main.ino), [fotografias](../img/), [diagrama no workspace](../CP2-TinyML/diagramaDeFuncionamento.png) e [documentação registrada no Git](https://github.com/victoriafpizza/cpCarrinho/blob/08da745ee9625781aa495e9dc2f7d84b97399af5/readme.md) | Tração 4WD, dois ESP32 e controle por joystick via MQTT. |
| CP2 | [Coleta HC-SR04](../CP2/) | Aquisição ultrassônica, captura serial e CSV histórico. |
| CP2-TinyML | [Integração, dados, política e simulação](../CP2-TinyML/) | Pipeline de proximidade preparado e simulado. Exportação Edge Impulse ausente. |
| Visão anterior | [GlobalSolution](../GlobalSolution/) | Webcam, OpenCV e checkpoint YOLOv8n com uma classe. |

A [entrega atual de iluminação](../GS/README.md) tem firmware, dados, modelo e testes próprios. A movimentação anterior do diagrama, já presente no workspace na abertura da tarefa, conserva os mesmos bytes do arquivo do Git.

# CP2 — TinyML, Edge Impulse e ESP32

Responsável: **Victoria Franceschini Pizza — RM550609**.

Projeto acadêmico para acrescentar classificação local de proximidade a um
carrinho 4WD com dois ESP32. O CP1 utiliza joystick, Wi-Fi/MQTT e quatro motores.
O CP2 prepara coleta→treinamento→teste→inferência→ação, mantendo os originais.
**Estado atual: dataset sintético preparado e integração de código pronta para
configuração; modelo real, compilação e funcionamento físico ainda pendentes.**

## Evolução e componentes

ESP32 do carrinho: AP/broker PicoMQTT, duas pontes H e quatro motores DC.
ESP32 do controle: joystick, Wi-Fi/PubSubClient, GPIOs X=34/Y=35. HC-SR04,
pilhas e chassi 4WD. Mapeamento do CP1 registrado em
[INTEGRACAO.md](software/carrinho_tinyml/INTEGRACAO.md). Original `main.ino`
reúne os dois programas e apresenta erros de sintaxe; permaneceu intacto.

## Funcionamento do sensor e coleta

TRIG envia pulso de 10 µs. Tempo de ECHO fornece distância aproximada em cm:
`duracao_us * 0.0343 / 2`. Timeout 30 ms; leituras fora de 2..400 cm inválidas.
Temperatura, ângulo, superfície e vibração alteram a medição. HC-SR04 convencional
usa 5 V: adaptar ECHO a 3,3 V, nunca ligá-lo diretamente à entrada ESP32.
22/23 eram exemplos no código anterior; conexões físicas ainda não confirmadas.

Copie coleta/config_coleta.example.h para config_coleta.h após conferir montagem.
Arduino IDE exige pasta de sketch com mesmo nome; copie o .ino e config para
uma pasta `coleta_hcsr04` para gravar. Durante coleta, rodas paradas. Instale:

```powershell
python -m pip install -r coleta/requirements.txt
python coleta/sensor.py --porta COM5 --classe LIVRE --segundos 30 --cenario objeto_plano_sessao1 --saida dataset/dados_reais/livre_sessao1.csv
```

Substitua COM5 pela porta verdadeira; feche Monitor Serial. Repita com ATENCAO
e PERIGO em posições verificadas com régua, novos arquivos e sessões. Rótulo
manual é preservado. Colete múltiplas distâncias, superfícies, ângulos e dias;
reserve sessões/cenários inteiros para teste. Capture também transições, mas
revise estratégia de rotulagem antes de usar janelas com classes misturadas.

## Dataset e preparação

`dataset/dados_simulados_cp2.csv` é uma cópia idêntica de
`C:/carrinho/cpCarrinho/CP2/dados_cp2.csv`, tratada como **sintética** conforme
solicitação. São 450 leituras (150/classe) com intervalo 150 ms; zero inválidas,
ausentes e duplicadas completas na validação. O nome foi ajustado só na cópia.
SHA256 original: `57aebd98e405d259d4e75e3d1c0a4e9ab89f213a7d159e39325a14855d984127`.

| Classe inicial | Faixa proposta | Ação TinyML |
|---|---|---|
| LIVRE | >60 cm | Joystick normal |
| ATENCAO | 25..60 cm | Metade do PWM no avanço |
| PERIGO | <25 cm | Bloqueia avanço; ré opcional após validação |

Limites rotulam o treinamento e precisam validação física. Isso é um classificador
supervisionado de proximidade; não comprova navegação complexa aprendida.
Distâncias repetidas em tempos diferentes são válidas; duplicados completos não.

```powershell
python coleta/preparar_dataset.py --entrada dataset/dados_simulados_cp2.csv --fonte simulado --saida dataset/nova_preparacao
```

Cada amostra: 10 leituras, `timestamp,distancia_cm`, 0..1350 ms, duração nominal
1500 ms. Não atravessa classe/lacuna nem sobrepõe janela. Divide cada trecho
temporal 80% para treino e descarta 10 leituras antes do teste: 36 janelas de
treino, 6 teste, 30 leituras descartadas. Sem leituras compartilhadas; manifesto
com linhas de origem, rótulos e hashes em dataset/validacao.json. As pastas
dataset/treino e dataset/teste já têm os arquivos para upload. A saída adicional
preparado_simulado conserva a execução original do preparador.

Há somente uma sequência por classe. A purga reduz correlação próxima, mas não
garante generalização. Para dados reais, substitua o pipeline sintético por:

```powershell
python coleta/preparar_dataset.py --fonte real --treino dataset/dados_reais/livre_s1.csv dataset/dados_reais/atencao_s1.csv dataset/dados_reais/perigo_s1.csv --teste dataset/dados_reais/livre_s2.csv dataset/dados_reais/atencao_s2.csv dataset/dados_reais/perigo_s2.csv --saida dataset/preparado_real_v1
```

Esses nomes ilustram sessões a coletar; não existem medições reais nesta entrega.
Não concatenar sessões com reset de timestamp. Arquivos existentes nunca são
sobrescritos pelo preparador. Simulador opcional cria somente arquivo novo:
`python coleta/simular_sensor_cp2.py --saida dataset/fixture_simulada.csv`.

## Edge Impulse e modelo

Studio está sem autenticação. Configuração proposta: projeto
`Carrinho-ESP32-TinyML-CP2`, Time series, distância, 6,6667 Hz, Raw Data,
Classification, janela/incremento 1500 ms; Dense 16→8→3, 50 épocas, LR 0,001.
São propostas, não uma execução. Seguir [configuracao.md](edge-impulse/configuracao.md)
e [treinamento.md](edge-impulse/treinamento.md). Confirmar rótulos e contagem após
upload; Test set separado. Resultados reais somente em
[resultados.md](edge-impulse/resultados.md). Accuracy, loss, matriz de confusão,
precision, recall, RAM/ROM e tempo de inferência **não obtidos**.

Depois de treinar/testar, exportar Arduino library no Deployment, preservar ZIP,
hash/versão e header real em modelo/. Inferência local chama run_classifier com
as constantes geradas. Nenhuma biblioteca ou inferência falsa foi incluída.

## ESP32 e comportamento

Sketch carrinho: software/carrinho_tinyml/carrinho_tinyml.ino. Sketch controle
separado: software/controle_cp2/controle_cp2.ino; controle funcional instalado
pode permanecer. Bibliotecas: core ESP32 3.x, PicoMQTT, ArduinoJson 7.x e modelo EI;
controle usa PubSubClient. Versões exatas pendentes. Confirme direção física do
avanço com rodas suspensas e defina CP2_FORWARD_SIGN (+1/-1).

Copiar config_local.example.h para config_local.h; preencher GPIOs reais,
header real, confirmação de pinos e CP2_ALLOW_REVERSE=0. Compile na placa exata.
Firmware impede compilação sem configuração/modelo; não inventa header nem pinos.
JSON/tópico, mapeamento e mistura diferencial do CP1 preservados.

Maior probabilidade determina classe; mínimo proposto 0,80. Falhas/baixa confiança,
leituras inválidas e perda de comandos solicitam parada. Watchdog 350 ms desde
último payload válido. Ré opcional reduzida apenas quando ambas rodas afastam.
Durante inferência síncrona, saída para motores zero. Veja detalhes e limitações
em INTEGRACAO.md. Janela 1,5 s pode reagir tarde: valide transições, tempo de
resposta e distância física de parada em baixa velocidade antes de demonstrar.

## Testes, evidências e reprodução

14 testes Python passaram: `python -m unittest discover -s testes -v`.
Não são testes do modelo nem do hardware. Testes C++ da política estão preparados
mas não executados. Não houve compilação ESP32, inferência embarcada, leitura
física, ensaio MQTT ou acionamento físico dos motores neste ambiente.
Logs/status em evidencias/; hashes dos originais para auditoria.
Seguir [roteiro_fisico.md](testes/roteiro_fisico.md) para cada teste e registro.

Passos restantes: confirmar hardware→coletar sessões reais→preparar dados→login
e upload verificado→treinar e Model Testing→exportar ZIP→configurar/compilar→
gravar carrinho→testar rodas suspensas→ensaiar baixa velocidade→registrar vídeo.
Vídeo em 14/10/2026; apresentação presencial em 21/10/2026.

## GitHub e versões

Repositório informado: https://github.com/victoriafpizza/cpCarrinho . Todos os novos
arquivos ficam em CP2-TinyML. Originais preservados; nenhum push feito.
Commits separados por coleta/dataset/documentação de treinamento/integração/testes.
O acesso Git foi resolvido concedendo escrita na pasta pai; os commits registram
somente arquivos de CP2-TinyML. O script commits.ps1 reproduz as etapas numa cópia
ainda não commitada e exige índice vazio. Não execute novamente se já commitadas.

v0.1 (12/10/2026): inspeção, dataset sintético validado, arquivos EI, coleta,
integração preparada, testes de dados e documentação. Modelo e hardware pendentes.
Próxima versão: treinamento/exportação reais, versões de dependências e evidências.

Fonte oficial de CSV: https://www.edgeimpulse.com/blog/import-your-data-as-csv/ .
PWM ESP32: https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html .

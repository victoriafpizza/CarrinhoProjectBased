# Roteiro de aceitação — todos os testes físicos pendentes

Antes de ligar: confirmar GND comum e alimentação, divisor/adaptador de ECHO
5 V→3,3 V, GPIOs e pontes H. Não conectar ECHO direto ao ESP32. Manter acesso
à desconexão da alimentação. Começar com rodas suspensas.

| Teste | Procedimento | Aceitação/evidência |
|---|---|---|
| HC-SR04 | Medir com régua em posições variadas e limites 25/60 cm | CSV serial real, erro e timeouts documentados |
| Entrada | Comparar janela serial vs arquivo/modelo | 10 cm, mesma ordem, ~150 ms, sem reescala |
| Inferência | Usar exemplo exportado e depois firmware | run_classifier OK; label/confiança/tempo registrados |
| Classes | Objetos nas 3 faixas, diversas superfícies | Probabilidades reais e falhas registradas |
| Joystick | Centro/frente/ré/curvas | Mantém mistura diferencial em LIVRE |
| ATENCAO | Mesmo comando em LIVRE e ATENCAO | PWM solicitado reduzido à metade no avanço |
| PERIGO | Mesmo comando com classe PERIGO | PWM 0 nos 4 motores no avanço |
| Ré | Liberar macro apenas após conferir sinal e entorno | Ambas rodas afastam, potência reduzida |
| MQTT | Confirmar tópico/JSON, desligar controle | Após 350 ms sem payload válido, PWM 0; medir atraso real |
| JSON inválido | Publicar x/y ausentes, fora de faixa ou texto | Para sem aproveitar comando antigo |
| Sensor inválido | Remover alimentação do sensor/sem retorno | Para; não preenche janela com valores inventados |
| Confiança/falha | Observar casos ambíguos e logs de erro reais | Para; não simular esse log como evidência de inferência |
| Transição | Aproximar obstáculo com velocidade baixa | Medir reação, distância de parada, mistura de janela |
| Energia | Variar bateria sob carga dentro das especificações | Sem resets perigosos; boot começa parado |

Salvar CSV/log serial, vídeo contínuo e fotos em evidencias/; screenshots reais
de Data acquisition, Train, Model Testing e Deployment em edge-impulse/prints/.
Cada registro: data, responsável, versão do código/modelo, placa, cenário, esperado,
observado, aprovado/reprovado. O vídeo deve mostrar COLETAR→TREINAR→TESTAR→
EMBARCAR→INFERIR→AGIR, distinguindo dados sintéticos e físicos.

Prazo vídeo: 14/10/2026; apresentação: 21/10/2026. Não marcar aceitação sem medição.

# Configuração proposta — ainda não aplicada

Consulta em 12/10/2026. Studio abriu https://studio.edgeimpulse.com/login.
Sem sessão autenticada: nenhum projeto criado, nenhum upload confirmado.

1. Faça login no Studio e crie `Carrinho-ESP32-TinyML-CP2`.
2. Data acquisition > Upload data: envie `dataset/treino/*.csv` como Training
   e `dataset/teste/*.csv` como Testing. Não use distribuição aleatória automática.
3. Um arquivo por amostra; cabeçalho `timestamp,distancia_cm`, timestamps relativos
   de 0 a 1350 ms em passos de 150 ms. Dez leituras representam duração nominal
   de 1500 ms. Nome `LIVRE.0000.csv` identifica a classe; se o importador não
   inferir o rótulo, selecione-o explicitamente por lote de classe.
4. Confirme 36 amostras Training (12 por classe) e 6 Testing (2 por classe).
   Abra exemplos das três classes e verifique eixo, unidade cm, intervalo 150 ms,
   timestamps e rótulos. Importação NÃO concluída até essa conferência.
5. Create impulse: Time series; frequência 6,6666667 Hz; window 1500 ms;
   window increase 1500 ms; Raw Data com eixo distancia_cm; Classification.
6. Se o Studio arredondar a frequência ou gerar 11 leituras, registre o ajuste
   real e adapte tanto exportação quanto firmware. Não use 7 Hz no hardware
   mantendo 150 ms sem revisar. Confira `EI_CLASSIFIER_INTERVAL_MS` e
   `EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE` na biblioteca gerada.
7. Raw Data > Save parameters > Generate features somente para o treino.

O importador CSV foi confirmado na fonte oficial:
https://www.edgeimpulse.com/blog/import-your-data-as-csv/
Formato binário alternativo: https://docs.edgeimpulse.com/reference/data-ingestion/data-acquisition-format

CLI opcional, após instalar a CLI oficial e autenticar:

```powershell
edge-impulse-uploader --category training dataset/treino/*.csv
edge-impulse-uploader --category testing dataset/teste/*.csv
```

No Windows, prefira upload no Studio caso o shell não expanda o glob para a CLI.
Consulte `edge-impulse-uploader --help` antes de usar; escolha o projeto correto.
Não grave API keys, cookies ou credenciais em arquivos versionados.

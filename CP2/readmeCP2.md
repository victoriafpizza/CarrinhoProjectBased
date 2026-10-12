# CP2 – Etapa 1: coleta real do HC-SR04

> **Status:** código de coleta preparado; aquisição física, dataset e validação ainda pendentes.
> Esta pasta é uma ADIÇÃO ao repositório do CP1. Não substituir `software/carrinho` nem `software/controle`.

## Hardware e cuidado com a ligação

- Sensor adotado provisoriamente: **HC-SR04**, informado pelo grupo.
- **TRIG 22 / ECHO 23 são somente EXEMPLOS no sketch**, pois os GPIOs reais não foram informados. Antes de alimentar o circuito, identifique as conexões e ajuste as constantes.
- Os GPIOs 22 e 23 não constam no mapeamento dos quatro motores do código do CP1, mas ainda é preciso conferir a montagem física.
- HC-SR04 convencional: VCC em 5 V, GND comum, TRIG em saída digital e **ECHO em entrada com adaptação do sinal 5 V para 3,3 V** (p. ex., divisor 1 kΩ em série com ECHO e 2 kΩ do GPIO ao GND). Não ligar ECHO diretamente ao ESP32.
- A expressão “sensor de luminosidade” não informa os pinos TRIG/ECHO: luminosidade (LDR) é outro sensor. Se o sensor real for LDR, será necessário outro código de coleta.

## Etapas de aquisição

1. Faça backup/commit do CP1 sem modificá-lo. Acrescente esta pasta `CP2-TinyML/`.
2. Confirme as conexões, ajuste TRIG/ECHO no sketch e conecte com segurança.
3. Abra `coleta/coleta_hcsr04.ino` no Arduino IDE; selecione sua placa ESP32 e grave somente esse sketch para a sessão de coleta. Não é o firmware final do carrinho.
4. Para registrar diretamente em arquivo, instale Python e `pyserial` (`pip install pyserial`), feche o Monitor Serial e execute, a partir da pasta `coleta`:
   `python capturar_serial.py --porta COM5 --saida ../dataset/dados_brutos.csv`
   Substitua COM5 pela porta real. Alternativamente, use o Monitor Serial em 115200 baud e copie somente as linhas CSV e o cabeçalho para o arquivo.
5. Com **obstáculos em posições reais**, digite `1` (LIVRE), `2` (ATENCAO) ou `3` (PERIGO) seguido de `s` para iniciar; `p` para pausar. O comando da classe pausa a gravação para evitar rótulos acidentais.
6. Classes iniciais propostas: LIVRE > 60 cm; ATENCAO entre 25 e 60 cm; PERIGO < 25 cm. Esses limites são **provisórios**: afaste/aproxime o objeto e rotule conforme a posição real, documentando distâncias e cenários. Evite registrar medidas fora da faixa correspondente ao rótulo.
7. Recolha diferentes distâncias, objetos, ângulos, superfícies e condições, **sem movimentar as rodas durante a aquisição inicial**. Meta sugerida: pelo menos 150 leituras válidas por classe, com múltiplas sessões independentes; isso é uma meta, não dados já coletados.
8. Verifique no CSV a distribuição de classes, valores fora de faixa, duplicações e timestamps reiniciados. Mantenha cada sessão identificável e separe treino/teste por sessão/cenário, evitando mistura de leituras vizinhas entre conjuntos.
9. Salve prints e vídeo da coleta. Depois é preciso preparar o formato de entrada escolhido no Edge Impulse e decidir janela temporal/recursos do modelo antes do treinamento.

## Formato do dataset

O arquivo `dataset/dados_brutos.csv` será criado somente a partir da serial real com as colunas:

`tempo_ms,distancia_cm,classe`

Não incluímos CSV com medições inventadas. `tempo_ms` é o tempo desde o último boot e pode reiniciar a cada sessão.

## Critério de conclusão da Etapa 1

- [ ] GPIOs reais e condicionamento elétrico verificados
- [ ] Leituras de distância obtidas do HC-SR04
- [ ] CSV real armazenado no repositório
- [ ] Classes e número de amostras documentados
- [ ] Prints/fotos da coleta registrados
- [ ] Commit da etapa de coleta realizado

## Próxima etapa

Preparar CSVs para o Edge Impulse, configurar o Impulse e treinar um classificador. A ação dos motores só será implementada depois que existir uma biblioteca exportada de um modelo realmente treinado.

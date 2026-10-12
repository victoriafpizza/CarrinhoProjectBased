
/*
 * CP2 - TinyML com ESP32
 * ETAPA 1 - COLETA DE DADOS
 *
 * Sensor: HC-SR04
 * Placa: ESP32
 * Comunicação: Serial 115200
 *
 * Classes:
 * LIVRE   - distância maior que 60 cm
 * ATENCAO - distância entre 25 e 60 cm
 * PERIGO  - distância menor que 25 cm
 *
 * Comandos:
 * 1 = selecionar LIVRE
 * 2 = selecionar ATENCAO
 * 3 = selecionar PERIGO
 * s = iniciar coleta
 * p = pausar coleta
 * q = finalizar coleta
 */

// ==========================================
// CONFIGURAÇÃO DOS PINOS
// ==========================================

// PINOS DE EXEMPLO!
// Confirmar as conexões reais antes de usar.

const int PIN_TRIG = 22;
const int PIN_ECHO = 23;

// ==========================================
// CONFIGURAÇÕES DA COLETA
// ==========================================

const unsigned long INTERVALO_COLETA = 150;

unsigned long ultimaColeta = 0;

bool coletando = false;

String classeAtual = "LIVRE";

// ==========================================
// LEITURA DO SENSOR ULTRASSÔNICO
// ==========================================

float lerDistanciaCM() {

  // Garante que o TRIG comece desligado
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);

  // Envia pulso de 10 microssegundos
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  // Mede a duração do pulso de retorno
  unsigned long duracao = pulseIn(
    PIN_ECHO,
    HIGH,
    30000
  );

  // Timeout ou ausência de retorno
  if (duracao == 0) {
    return -1;
  }

  // Velocidade aproximada do som: 0,0343 cm/us
  // Divide por 2: ida e volta do sinal
  float distancia = duracao * 0.0343 / 2.0;

  return distancia;
}

// ==========================================
// COMANDOS RECEBIDOS PELO PYTHON
// ==========================================

void processarComando(char comando) {

  switch (comando) {

    case '1':
      classeAtual = "LIVRE";
      Serial.println("# Classe: LIVRE");
      break;

    case '2':
      classeAtual = "ATENCAO";
      Serial.println("# Classe: ATENCAO");
      break;

    case '3':
      classeAtual = "PERIGO";
      Serial.println("# Classe: PERIGO");
      break;

    case 's':
    case 'S':
      coletando = true;
      Serial.println("# Coleta iniciada");
      break;

    case 'p':
    case 'P':
      coletando = false;
      Serial.println("# Coleta pausada");
      break;

    case 'q':
    case 'Q':
      coletando = false;
      Serial.println("# Coleta encerrada");
      break;

    default:
      Serial.println("# Comando desconhecido");
      break;
  }
}

// ==========================================
// CONFIGURAÇÃO INICIAL
// ==========================================

void setup() {

  Serial.begin(115200);

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  digitalWrite(PIN_TRIG, LOW);

  delay(1000);

  Serial.println("# CP2 - TinyML ESP32");
  Serial.println("# Sensor HC-SR04");
  Serial.println("# Sistema de coleta pronto");

  Serial.println("# 1 = LIVRE");
  Serial.println("# 2 = ATENCAO");
  Serial.println("# 3 = PERIGO");
  Serial.println("# s = iniciar");
  Serial.println("# p = pausar");
  Serial.println("# q = finalizar");
}

// ==========================================
// LOOP PRINCIPAL
// ==========================================

void loop() {

  // Verifica comandos enviados pelo Python
  while (Serial.available() > 0) {

    char comando = Serial.read();

    if (comando != '\n' && comando != '\r') {
      processarComando(comando);
    }
  }

  // Se não estiver coletando, não registra dados
  if (!coletando) {
    return;
  }

  // Controle de intervalo entre medições
  if (millis() - ultimaColeta < INTERVALO_COLETA) {
    return;
  }

  ultimaColeta = millis();

  // Realiza leitura real do HC-SR04
  float distancia = lerDistanciaCM();

  // Ignora medições inválidas
  if (distancia < 2 || distancia > 400) {
    Serial.println("# Leitura invalida");
    return;
  }

  // Envia os dados no formato CSV
  // tempo_ms,distancia_cm,classe

  Serial.print(millis());
  Serial.print(",");

  Serial.print(distancia, 2);
  Serial.print(",");

  Serial.println(classeAtual);
}

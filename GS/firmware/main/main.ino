#include <Arduino.h>
#include <Bluepad32.h>
#include <esp_arduino_version.h>

#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "Selecione uma placa ESP32 classica: o LDR usa GPIO36 (ADC1)."
#endif

#if !defined(ESP_ARDUINO_VERSION_MAJOR) || (ESP_ARDUINO_VERSION_MAJOR != 2 && ESP_ARDUINO_VERSION_MAJOR != 3)
#error "Este sketch implementa as APIs LEDC do Arduino-ESP32 Core 2.x e 3.x."
#endif

// Pinagem da versão atual da Global Solution.
constexpr int ENA = 19;
constexpr int IN1 = 18;
constexpr int IN2 = 5;
constexpr int IN3 = 4;
constexpr int IN4 = 21;
constexpr int ENB = 15;
constexpr int PINO_LDR = 36;
constexpr int PINO_LED = 22;

constexpr int ADC_MAX = 4095;
constexpr int LIMITE_ESCURO = 1200;
constexpr int LIMITE_CLARO = 1600;
constexpr bool SENSOR_INVERTIDO = false;
constexpr int AMOSTRAS_LDR = 8;
constexpr uint32_t INTERVALO_LDR_MS = 25;
constexpr uint32_t INTERVALO_LOG_MS = 1000;

constexpr int VELOCIDADE_NORMAL = 255;
constexpr int VELOCIDADE_REDUZIDA = 210;
constexpr int PWM_FREQUENCIA = 5000;
constexpr int PWM_RESOLUCAO = 8;
constexpr uint32_t TIMEOUT_CONTROLE_MS = 400;

struct Motor {
  int enable;
  int entradaPositiva;
  int entradaNegativa;
  int canal;
  int direcao;
  int pwm;
  bool pwmConfigurado;
};

Motor motorEsquerdo{ENA, IN1, IN2, 0, 0, 0, false};
Motor motorDireito{ENB, IN3, IN4, 1, 0, 0, false};
bool motoresOperacionais = false;

struct Comando {
  int esquerda;
  int direita;
};

ControllerPtr controleAtivo = nullptr;
Comando comando{};
bool comandoValido = false;
uint32_t ultimoComandoMs = 0;

bool escuro = true;
bool leituraValida = false;
int leituraLdr = 0;
int leituraNormalizada = 0;
uint32_t ultimaLeituraMs = 0;
uint32_t ultimoLogMs = 0;

bool escreverPwm(const Motor& motor, int pwm) {
#if ESP_ARDUINO_VERSION_MAJOR == 3
  return ledcWrite(motor.enable, pwm);
#else
  ledcWrite(motor.canal, pwm);
  return true;
#endif
}

void desabilitarMotor(Motor& motor) {
  if (motor.pwmConfigurado) {
    escreverPwm(motor, 0);
  }
  digitalWrite(motor.entradaPositiva, LOW);
  digitalWrite(motor.entradaNegativa, LOW);
  motor.direcao = 0;
  motor.pwm = 0;
}

bool configurarMotor(Motor& motor) {
#if ESP_ARDUINO_VERSION_MAJOR == 3
  motor.pwmConfigurado = ledcAttach(motor.enable, PWM_FREQUENCIA, PWM_RESOLUCAO);
#else
  motor.pwmConfigurado = ledcSetup(motor.canal, PWM_FREQUENCIA, PWM_RESOLUCAO) > 0;
  if (motor.pwmConfigurado) {
    ledcAttachPin(motor.enable, motor.canal);
  }
#endif
  return motor.pwmConfigurado && escreverPwm(motor, 0);
}

void prepararPinos(Motor& motor) {
  pinMode(motor.enable, OUTPUT);
  digitalWrite(motor.enable, LOW);
  pinMode(motor.entradaPositiva, OUTPUT);
  pinMode(motor.entradaNegativa, OUTPUT);
  desabilitarMotor(motor);
}

int velocidadePermitida() {
  return escuro ? VELOCIDADE_REDUZIDA : VELOCIDADE_NORMAL;
}

bool aplicarMotor(Motor& motor, int sentido, int limite) {
  const int pwm = sentido == 0 ? 0 : limite;
  if (motor.direcao == sentido && motor.pwm == pwm) {
    return true;
  }

  // Retira PWM antes de inverter e desativa ambas as entradas antes de trocar o sentido.
  if (motor.direcao != sentido) {
    if (!escreverPwm(motor, 0)) {
      return false;
    }
    digitalWrite(motor.entradaPositiva, LOW);
    digitalWrite(motor.entradaNegativa, LOW);
    if (sentido > 0) {
      digitalWrite(motor.entradaPositiva, HIGH);
    } else if (sentido < 0) {
      digitalWrite(motor.entradaNegativa, HIGH);
    }
  }
  if (!escreverPwm(motor, pwm)) {
    return false;
  }
  motor.direcao = sentido;
  motor.pwm = pwm;
  return true;
}

void aplicarComando(Comando movimento) {
  if (!motoresOperacionais) {
    return;
  }
  const int limite = velocidadePermitida();
  if (!aplicarMotor(motorEsquerdo, movimento.esquerda, limite) ||
      !aplicarMotor(motorDireito, movimento.direita, limite)) {
    motoresOperacionais = false;
    desabilitarMotor(motorEsquerdo);
    desabilitarMotor(motorDireito);
    Serial.println("[ROTA LIVRE] Erro ao escrever PWM; tracao bloqueada ate reiniciar");
  }
}

void registrarLuz(uint32_t agora) {
  ultimoLogMs = agora;
  Serial.printf("[ROTA LIVRE] LDR: %d | Ajustado: %d | Estado: %s | PWM limite: %d | LED: %s%s\n",
                leituraLdr, leituraNormalizada, escuro ? "ESCURO" : "CLARO",
                velocidadePermitida(), escuro ? "ON" : "OFF",
                leituraValida ? "" : " | ADC invalido ou no extremo");
}

void atualizarLuz(uint32_t agora, bool inicial) {
  if (!inicial && agora - ultimaLeituraMs < INTERVALO_LDR_MS) {
    return;
  }
  ultimaLeituraMs = agora;
  int soma = 0;
  bool dentroDaFaixa = true;
  for (int i = 0; i < AMOSTRAS_LDR; ++i) {
    const int amostra = analogRead(PINO_LDR);
    if (amostra < 0 || amostra > ADC_MAX) {
      dentroDaFaixa = false;
    } else {
      soma += amostra;
    }
  }
  const bool estadoAnterior = escuro;
  const bool validadeAnterior = leituraValida;
  leituraLdr = dentroDaFaixa ? soma / AMOSTRAS_LDR : -1;
  leituraValida = leituraLdr > 0 && leituraLdr < ADC_MAX;
  leituraNormalizada = leituraValida && SENSOR_INVERTIDO ? ADC_MAX - leituraLdr : leituraLdr;

  // Na partida em faixa intermediária, adota o limite reduzido até identificar luz adequada.
  if (!leituraValida || leituraNormalizada < LIMITE_ESCURO) {
    escuro = true;
  } else if (leituraNormalizada > LIMITE_CLARO) {
    escuro = false;
  }
  digitalWrite(PINO_LED, escuro ? HIGH : LOW);
  if (inicial || estadoAnterior != escuro || validadeAnterior != leituraValida ||
      agora - ultimoLogMs >= INTERVALO_LOG_MS) {
    registrarLuz(agora);
  }
}

void aoConectarControle(ControllerPtr controle) {
  if (controleAtivo == nullptr) {
    controleAtivo = controle;
    comandoValido = false;
    Serial.println("[ROTA LIVRE] Controle conectado; aguardando dados do gamepad");
  }
}

void aoDesconectarControle(ControllerPtr controle) {
  if (controle == controleAtivo) {
    controleAtivo = nullptr;
    comandoValido = false;
    comando = {};
    aplicarComando({});
    Serial.println("[ROTA LIVRE] Controle desconectado; motores parados");
  }
}

Comando lerComando(ControllerPtr controle) {
  const bool frente = controle->y();
  const bool tras = controle->a();
  const bool direita = controle->b();
  const bool esquerda = controle->x();
  if (frente + tras + direita + esquerda != 1) {
    return {};
  }
  if (frente) {
    return {1, 1};
  }
  if (tras) {
    return {-1, -1};
  }
  if (direita) {
    return {1, -1};
  }
  return {-1, 1};
}

void atualizarControle(uint32_t agora) {
  if (!controleAtivo || !controleAtivo->isConnected() || !controleAtivo->isGamepad()) {
    comandoValido = false;
    comando = {};
    return;
  }
  if (controleAtivo->hasData()) {
    comando = lerComando(controleAtivo);
    ultimoComandoMs = agora;
    comandoValido = true;
  }
  if (comandoValido && agora - ultimoComandoMs >= TIMEOUT_CONTROLE_MS) {
    comandoValido = false;
    comando = {};
    aplicarComando({});
    Serial.println("[ROTA LIVRE] Timeout do controle; motores parados");
  }
}

void setup() {
  Serial.begin(115200);
  prepararPinos(motorEsquerdo);
  prepararPinos(motorDireito);
  pinMode(PINO_LED, OUTPUT);
  digitalWrite(PINO_LED, LOW);
  pinMode(PINO_LDR, INPUT);
  analogReadResolution(12);

  const bool esquerdaOk = configurarMotor(motorEsquerdo);
  const bool direitaOk = configurarMotor(motorDireito);
  motoresOperacionais = esquerdaOk && direitaOk;
  if (!motoresOperacionais) {
    desabilitarMotor(motorEsquerdo);
    desabilitarMotor(motorDireito);
    Serial.println("[ROTA LIVRE] Erro na inicializacao PWM; tracao bloqueada");
  }

  atualizarLuz(millis(), true);
  BP32.setup(&aoConectarControle, &aoDesconectarControle);
  Serial.println("[ROTA LIVRE] Aguardando gamepad Xbox");
}

void loop() {
  BP32.update();
  const uint32_t agora = millis();
  atualizarControle(agora);
  // Para antes de coletar/amostrar ou emitir logs quando não há mais um comando válido.
  if (!comandoValido || (comando.esquerda == 0 && comando.direita == 0)) {
    aplicarComando({});
    atualizarLuz(agora, false);
    return;
  }
  atualizarLuz(agora, false);
  aplicarComando(comando);
}

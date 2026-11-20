#include <Arduino.h>

#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "Selecione um ESP32 classico e confirme a montagem do GPIO34 antes de gravar."
#endif

constexpr int LDR_PIN = 34;
constexpr int ADC_MAX = 4095;
constexpr uint32_t SAMPLE_INTERVAL_MS = 200;
constexpr size_t SAMPLE_COUNT = 5;
uint32_t lastSample = 0;

int medianAdc() {
  int samples[SAMPLE_COUNT];
  for (size_t i = 0; i < SAMPLE_COUNT; ++i) {
    samples[i] = analogRead(LDR_PIN);
    delay(2);
  }
  for (size_t i = 1; i < SAMPLE_COUNT; ++i) {
    const int value = samples[i];
    size_t index = i;
    while (index > 0 && samples[index - 1] > value) {
      samples[index] = samples[index - 1];
      --index;
    }
    samples[index] = value;
  }
  return samples[SAMPLE_COUNT / 2];
}

void setup() {
  Serial.begin(115200);
  pinMode(LDR_PIN, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(LDR_PIN, ADC_ATTEN_DB_11);
  lastSample = millis();
}

void loop() {
  const uint32_t now = millis();
  if (now - lastSample < SAMPLE_INTERVAL_MS) {
    return;
  }
  lastSample = now;
  const int adc = medianAdc();
  const char* status = adc > 0 && adc < ADC_MAX ? "OK" : "LIMITE_OU_INVALIDO";
  Serial.printf("LDR,%lu,%d,%s\n", static_cast<unsigned long>(now), adc, status);
}

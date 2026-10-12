// PROGRAMA 2 - ESP32 DO CONTROLE / JOYSTICK SHIELD
// ============================================================
// Este é o código responsável pelo segundo ESP32.
//
// Ele lê os movimentos do joystick conectado à shield,
// transforma os valores em uma escala de -255 até 255,
// conecta-se à rede Wi-Fi criada pelo carrinho e envia
// os valores X e Y através de MQTT.
// ============================================================


// Biblioteca responsável pela conexão Wi-Fi.
#include <WiFi.h>


// Biblioteca responsável pelo funcionamento do ESP32
// como cliente MQTT.
#include <PubSubClient.h>


// Biblioteca utilizada para criar a mensagem JSON
// contendo os valores X e Y.
#include <ArduinoJson.h>


// Definição dos pinos analógicos do Joystick

// GPIO 34 recebe o valor analógico do eixo horizontal X.
const int pinX = 34; // Eixo X


// GPIO 35 recebe o valor analógico do eixo vertical Y.
const int pinY = 35; // Eixo Y


// Credenciais da rede Wi-Fi gerada pelo carrinho

// Nome da rede Wi-Fi criada pelo primeiro ESP32.
const char* ssid = "ESP32_Rede_MQTT";


// Senha utilizada para conectar à rede do carrinho.
const char* password = "senha12345";


// IP do servidor MQTT (Broker no carrinho)

// Endereço padrão do ESP32 quando trabalha
// no modo Access Point.
const char* mqtt_server = "192.168.4.1"; // IP padrão do Access Point do ESP32


// Porta padrão utilizada pelo protocolo MQTT.
const int mqtt_port = 1883;


// Cria um cliente de rede Wi-Fi utilizado
// posteriormente pela biblioteca MQTT.
WiFiClient espClient;


// Cria o cliente MQTT utilizando a conexão Wi-Fi acima.
PubSubClient client(espClient);


// ============================================================
// FUNÇÃO DE CONEXÃO WI-FI
// ============================================================
// Responsável por conectar o ESP32 do joystick
// à rede criada pelo ESP32 do carrinho.
// ============================================================

void setupWiFi() {


  // Pequeno atraso antes de iniciar a conexão.
  delay(10);


  // Mostra no Monitor Serial a rede que
  // o ESP32 tentará acessar.
  Serial.print("Conectando à rede Wi-Fi: ");

  Serial.println(ssid);


  // Inicia a tentativa de conexão à rede
  // utilizando SSID e senha definidos anteriormente.
  WiFi.begin(ssid, password);


  // Enquanto a conexão não for estabelecida,
  // o código permanece neste loop.
  while (WiFi.status() != WL_CONNECTED) {


    // Aguarda meio segundo entre verificações.
    delay(500);


    // Imprime pontos no Monitor Serial indicando
    // que ainda está tentando conectar.
    Serial.print(".");

  }


  // Quando sai do while, significa que a conexão
  // Wi-Fi foi concluída.
  Serial.println("\nWi-Fi conectado!");


  // Mostra o endereço IP recebido pelo ESP32 controle.
  Serial.print("Endereço IP obtido: ");

  Serial.println(WiFi.localIP());

}


// ============================================================
// FUNÇÃO DE RECONEXÃO MQTT
// ============================================================
// Garante que o controle continue conectado ao Broker MQTT.
// Caso a conexão seja perdida, tenta novamente automaticamente.
// ============================================================

void reconnectMQTT() {


  // Permanece tentando enquanto o cliente MQTT
  // não estiver conectado.
  while (!client.connected()) {


    // Informação exibida para diagnóstico.
    Serial.print("Tentando conexão MQTT...");


    // Tenta conectar usando um ID de cliente único

    // ESP32_Joystick_Client identifica este dispositivo
    // dentro da comunicação MQTT.
    if (client.connect("ESP32_Joystick_Client")) {


      // Executado caso a conexão tenha funcionado.
      Serial.println("Conectado ao Broker MQTT do carrinho!");


    } else {


      // Caso a conexão falhe, exibe uma mensagem.
      Serial.print("Falha na conexão. Código de erro=");


      // client.state() retorna o código do erro MQTT.
      Serial.print(client.state());


      // Informa que será realizada nova tentativa.
      Serial.println(". Tentando novamente em 2 segundos...");


      // Aguarda dois segundos antes da próxima tentativa.
      delay(2000);

    }

  }

}


// ============================================================
// SETUP DO ESP32 DO JOYSTICK
// ============================================================

void setup() {


  // Inicializa o Monitor Serial.
  Serial.begin(115200);


  // Configuração dos pinos do Joystick como entradas

  // Como o joystick gera sinais analógicos,
  // esses GPIOs são utilizados como entrada.
  pinMode(pinX, INPUT);

  pinMode(pinY, INPUT);


  // Conecta ao Wi-Fi e configura o cliente MQTT

  // Chama a função responsável pela conexão com
  // a rede criada pelo carrinho.
  setupWiFi();


  // Informa ao cliente MQTT qual é o endereço
  // e a porta do Broker.
  client.setServer(mqtt_server, mqtt_port);

}


// ============================================================
// LOOP DO ESP32 DO JOYSTICK
// ============================================================

void loop() {


  // Verifica se a comunicação MQTT está ativa.
  if (!client.connected()) {


    // Caso tenha sido perdida, tenta reconectar.
    reconnectMQTT();

  }


  // Mantém a comunicação MQTT funcionando.
  client.loop();


  // Lê os valores analógicos brutos (0 a 4095 no ESP32)

  // O conversor ADC do ESP32 retorna valores
  // entre aproximadamente 0 e 4095.
  int valorBrutoX = analogRead(pinX);

  int valorBrutoY = analogRead(pinY);


  // Mapeia o intervalo de 0..4095 para -255..255

  // Nota: A inversão dos limites no mapa permite ajustar o sentido do movimento se necessário

  // Converte a leitura do joystick para a mesma escala
  // utilizada pelo controle PWM dos motores.
  int mapX = map(valorBrutoX, 0, 4095, -255, 255);

  int mapY = map(valorBrutoY, 0, 4095, -255, 255);


  // Aplica uma zona morta central para evitar ruidos do potenciômetro parado

  // Um joystick físico dificilmente retorna exatamente zero
  // quando está no centro.
  //
  // Por isso, qualquer valor pequeno entre aproximadamente
  // -19 e +19 é considerado zero.
  //
  // Isso evita que o carrinho se mova sozinho por pequenos
  // ruídos elétricos ou imprecisão do joystick.
  if (abs(mapX) < 20) mapX = 0;

  if (abs(mapY) < 20) mapY = 0;


  // Monta a estrutura JSON com as chaves "x" e "y" esperadas pelo carrinho

  // Cria um pequeno documento JSON com espaço suficiente
  // para armazenar os dois valores.
  StaticJsonDocument<128> doc;


  // Insere a posição horizontal do joystick.
  doc["x"] = mapX;


  // Insere a posição vertical do joystick.
  doc["y"] = mapY;


  // Cria um vetor de caracteres onde a mensagem
  // JSON final será armazenada.
  char buffer[128];


  // Transforma o documento JSON em texto para
  // que possa ser enviado através do MQTT.
  serializeJson(doc, buffer);


  // Publica a mensagem no tópico MQTT padrão recebido pelo carrinho

  // Envia o JSON para exatamente o mesmo tópico
  // que o ESP32 do carrinho está monitorando.
  client.publish("carrinho/joystick", buffer);


  // Exibe no Monitor Serial a mensagem que foi enviada.
  Serial.print("Enviado payload JSON: ");

  Serial.println(buffer);


  // Intervalo de transmissão (50ms para boa responsividade nos comandos)

  // Aguarda 50 milissegundos antes de realizar
  // uma nova leitura e transmissão.
  //
  // Isso corresponde a aproximadamente 20 atualizações
  // de comando por segundo.
  delay(50);

}

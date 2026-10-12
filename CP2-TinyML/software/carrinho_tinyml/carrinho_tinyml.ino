// Nova versão do PROGRAMA 1 do CP1. Requer biblioteca REAL exportada do EI.
#include <Arduino.h>
#include <initializer_list>
#include <math.h>
#include <cstring>
#include <WiFi.h>
#include <PicoMQTT.h>
#include <ArduinoJson.h>
#include <esp_arduino_version.h>
#include "config_local.h"
#include "policy.h"
#if !defined(CP2_PINS_CONFIRMED) || CP2_PINS_CONFIRMED != 1
#error "Confirmar GPIOs e divisor ECHO antes de compilar"
#endif
#ifndef CP2_EI_HEADER
#error "Definir header real da biblioteca Edge Impulse exportada"
#endif
#include CP2_EI_HEADER
#if ESP_ARDUINO_VERSION_MAJOR < 3
#error "Esta versão preserva PWM por pino do CP1 e requer Arduino-ESP32 3.x"
#endif
static_assert(CP2_FORWARD_SIGN==1 || CP2_FORWARD_SIGN==-1,"Confirmar sentido de avanço");
static_assert(EI_CLASSIFIER_RAW_SAMPLES_PER_FRAME==1,"Modelo deve usar só distancia_cm");
static_assert(EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE==10,"Reexportar para 10 leituras/1500ms ou revisar aquisição");
static_assert(EI_CLASSIFIER_LABEL_COUNT==3,"Modelo deve conter três classes");
constexpr int motorPins[]={25,26,27,13,12,14,15,2,4,18,19,21};
constexpr bool conflict(int p){for(int m:motorPins)if(m==p)return true;return false;}
static_assert(CP2_PIN_TRIG!=CP2_PIN_ECHO && !conflict(CP2_PIN_TRIG) && !conflict(CP2_PIN_ECHO),"GPIO do sensor conflita com motores");
const char* ap_ssid="ESP32_Rede_MQTT";
const char* ap_password="senha12345";
PicoMQTT::Server mqtt_server;
float features[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];
size_t count=0;uint32_t nextSample=0,lastCommand=0,lastPrediction=0;
int commandX=0,commandY=0;bool commandOk=false,modelOk=false,pwmOk=false;
Proximity proximity=Proximity::Unknown;
constexpr uint32_t COMMAND_TIMEOUT_MS=350,MODEL_TIMEOUT_MS=1800;
void motor(int speed,int a,int b,int pwm){
    digitalWrite(a,speed>0?HIGH:LOW);digitalWrite(b,speed<0?HIGH:LOW);ledcWrite(pwm,abs(speed));
}
void drive(Drive d){
    motor(d.left,12,14,13);motor(d.left,19,21,18);
    motor(d.right,26,27,25);motor(d.right,2,4,15);
}
void stop(){drive({0,0});}
void invalidate(){count=0;modelOk=false;proximity=Proximity::Unknown;stop();}
void apply(){
    uint32_t now=millis();
    bool healthy=pwmOk && commandOk && modelOk && WiFi.softAPgetStationNum()>0 &&
      fresh(now,lastCommand,COMMAND_TIMEOUT_MS) && fresh(now,lastPrediction,MODEL_TIMEOUT_MS);
    Drive d=gate(constrain(commandY+commandX,-255,255),constrain(commandY-commandX,-255,255),
        proximity,healthy,CP2_ALLOW_REVERSE,CP2_FORWARD_SIGN);
    drive(d);
}
float readDistance(){
    digitalWrite(CP2_PIN_TRIG,LOW);delayMicroseconds(2);
    digitalWrite(CP2_PIN_TRIG,HIGH);delayMicroseconds(10);digitalWrite(CP2_PIN_TRIG,LOW);
    unsigned long us=pulseIn(CP2_PIN_ECHO,HIGH,30000);
    return us?us*0.0343f/2.0f:-1.0f;
}
void infer(){
    // Para durante inferência síncrona: comando anterior não continua sem watchdog.
    stop();signal_t signal;ei_impulse_result_t result={};
    if(numpy::signal_from_buffer(features,EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE,&signal)!=0){invalidate();return;}
    uint32_t start=micros();EI_IMPULSE_ERROR err=run_classifier(&signal,&result,false);
    if(err!=EI_IMPULSE_OK){invalidate();return;}
    float best=-1;const char* name=nullptr;
    for(size_t i=0;i<EI_CLASSIFIER_LABEL_COUNT;i++){
        float v=result.classification[i].value;
        if(!isfinite(v)||v<0||v>1){invalidate();return;}
        if(v>best){best=v;name=result.classification[i].label;}
    }
    if(!name || best<0.80f){invalidate();return;}
    proximity=strcmp(name,"LIVRE")==0?Proximity::Livre:strcmp(name,"ATENCAO")==0?Proximity::Atencao:strcmp(name,"PERIGO")==0?Proximity::Perigo:Proximity::Unknown;
    modelOk=proximity!=Proximity::Unknown;lastPrediction=millis();
    Serial.printf("TinyML,%s,%.4f,%lu_us\n",name,best,(unsigned long)(micros()-start));
}
void setup(){
    Serial.begin(115200);
    for(int p:{26,27,12,14,2,4,19,21}){pinMode(p,OUTPUT);digitalWrite(p,LOW);}
    pwmOk=true;for(int p:{25,13,15,18}){if(!ledcAttach(p,5000,8))pwmOk=false;ledcWrite(p,0);}
    pinMode(CP2_PIN_TRIG,OUTPUT);digitalWrite(CP2_PIN_TRIG,LOW);pinMode(CP2_PIN_ECHO,INPUT);
    if(fabsf(EI_CLASSIFIER_INTERVAL_MS-150.0f)>1.0f){Serial.println("Intervalo modelo incompatível");pwmOk=false;}
    if(!WiFi.softAP(ap_ssid,ap_password))pwmOk=false;
    mqtt_server.subscribe("carrinho/joystick",[](const char*,const char* payload){
        JsonDocument doc;
        if(deserializeJson(doc,payload) || !doc["x"].is<int>() || !doc["y"].is<int>()){
            commandOk=false;stop();return;
        }
        int x=doc["x"],y=doc["y"];
        if(x < -255 || x > 255 || y < -255 || y > 255){commandOk=false;stop();return;}
        commandX=x;commandY=y;commandOk=true;lastCommand=millis();apply();
    });
    mqtt_server.begin();nextSample=millis();stop();
}
void loop(){
    mqtt_server.loop();apply();uint32_t now=millis();
    if(int32_t(now-nextSample)<0)return;
    if(uint32_t(now-nextSample)>15){invalidate();nextSample=now;}
    nextSample+=150;
    float d=readDistance();
    if(!isfinite(d)||d<2||d>400){invalidate();return;}
    features[count++]=d;
    if(count==EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE){infer();count=0;apply();}
}

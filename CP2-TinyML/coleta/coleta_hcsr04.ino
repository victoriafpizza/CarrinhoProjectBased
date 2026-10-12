#include <Arduino.h>
#include "config_coleta.h"
#if !defined(CP2_PINS_CONFIRMED) || CP2_PINS_CONFIRMED != 1
#error "Confirmar GPIOs reais e proteção ECHO em config_coleta.h"
#endif
bool active=false;const char* label="LIVRE";uint32_t nextRead=0;
void setup(){Serial.begin(115200);pinMode(CP2_PIN_TRIG,OUTPUT);digitalWrite(CP2_PIN_TRIG,LOW);pinMode(CP2_PIN_ECHO,INPUT);}
void loop(){
 while(Serial.available()){
   char c=Serial.read();
   if(c=='1'||c=='2'||c=='3'){active=false;label=c=='1'?"LIVRE":c=='2'?"ATENCAO":"PERIGO";}
   if(c=='s'){active=true;nextRead=millis();}
   if(c=='p'||c=='q')active=false;
 }
 uint32_t now=millis();if(!active || int32_t(now-nextRead)<0)return;
 if(uint32_t(now-nextRead)>15){Serial.println("# INVALID timing");nextRead=now;}
 nextRead+=150;
 digitalWrite(CP2_PIN_TRIG,LOW);delayMicroseconds(2);digitalWrite(CP2_PIN_TRIG,HIGH);delayMicroseconds(10);digitalWrite(CP2_PIN_TRIG,LOW);
 unsigned long us=pulseIn(CP2_PIN_ECHO,HIGH,30000);float d=us*0.0343f/2.0f;
 if(!us||d<2||d>400){Serial.println("# INVALID sensor");return;}
 Serial.printf("%lu,%.2f,%s\n",(unsigned long)now,d,label);
}

#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <RTClib.h>
#include <ESP32Servo.h>

// ===== WiFi =====
const char* WIFI_SSID = "ANGELO";
const char* WIFI_PASS = "omcvlacp17j";

// ===== GPIOs Semáforo =====
const int LED_ROJO=16, LED_AMARILLO=17, LED_VERDE=18;
uint32_t T_ROJO=8000, T_VERDE=9000, T_AMARILLO=2000;
enum TL{ROJO,VERDE,AMARILLO}; TL st=ROJO; uint32_t t0; bool running=false;

// ===== LCD / RTC =====
LiquidCrystal_I2C lcd(0x27,16,2);
RTC_DS3231 rtc; bool rtc_ok=false;
bool lcd_on = true;

// ===== Servos =====
Servo s1, s2; const int SERVO1=25, SERVO2=26; const int A_OPEN=45, A_CLOSE=0; bool opened=false;
int servo1Angle=A_CLOSE, servo2Angle=A_CLOSE; bool servosAttached=false;

void idleServoPins(){
  digitalWrite(SERVO1, LOW);
  digitalWrite(SERVO2, LOW);
  pinMode(SERVO1, OUTPUT);
  pinMode(SERVO2, OUTPUT);
}

void attachServos(){
  if(!servosAttached){
    s1.attach(SERVO1, 500, 2400);
    s2.attach(SERVO2, 500, 2400);
    s1.write(servo1Angle);
    s2.write(servo2Angle);
    servosAttached=true;
    delay(150);
  }
}
void detachServos(){
  if(servosAttached && !opened){
    s1.detach();
    s2.detach();
    servosAttached=false;
    idleServoPins();
  }
}
void smoothTo(Servo &s,int &current,int toA){
  int fromA=current;
  if(fromA==toA){ s.write(toA); return; }
  int step=(toA>=fromA)?1:-1;
  for(int a=fromA;a!=toA;a+=step){ s.write(a); delay(6);} s.write(toA);
  current=toA;
}
void setOpen(bool on){
  if(on && !opened){
    attachServos();
    smoothTo(s1,servo1Angle,A_OPEN);
    smoothTo(s2,servo2Angle,A_OPEN);
    opened=true;
  }
  else if(!on && opened){
    attachServos();
    smoothTo(s1,servo1Angle,A_CLOSE);
    smoothTo(s2,servo2Angle,A_CLOSE);
    opened=false;
    detachServos();
  }
  else if(!on){
    detachServos();
  }
}

// ===== Helpers =====
String stText(){ return st==ROJO?"ROJO":(st==VERDE?"VERDE":"AMARILLO"); }
uint32_t dur(){ return st==ROJO?T_ROJO:(st==VERDE?T_VERDE:T_AMARILLO); }
String nowIso(){ if(!rtc_ok) return "----"; DateTime n=rtc.now(); char b[25]; snprintf(b,25,"%04d-%02d-%02dT%02d:%02d:%02d",
  n.year(),n.month(),n.day(),n.hour(),n.minute(),n.second()); return String(b); }
String pad16(String s){ if(s.length()>16)s=s.substring(0,16); while(s.length()<16)s+=' '; return s; }
bool parseISO(String iso, DateTime &out){
  iso.trim(); if(iso.length()<19) return false;
  int Y=iso.substring(0,4).toInt(), M=iso.substring(5,7).toInt(), D=iso.substring(8,10).toInt();
  int h=iso.substring(11,13).toInt(), m=iso.substring(14,16).toInt(), s=iso.substring(17,19).toInt();
  if(Y<2000||M<1||M>12||D<1||D>31||h<0||h>23||m<0||m>59||s<0||s>59) return false;
  out=DateTime(Y,M,D,h,m,s); return true;
}

// ===== Web =====
WebServer server(80);
void addCORS(){ server.sendHeader("Access-Control-Allow-Origin", "*");
                server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
                server.sendHeader("Access-Control-Allow-Headers", "Content-Type"); }
void sendJSON(const String& j){ addCORS(); server.send(200,"application/json",j); }
void sendOK(){ addCORS(); server.send(200,"text/plain","OK"); }
void sendBad(const String& m){ addCORS(); server.send(400,"text/plain",m); }
void handle_options(){ addCORS(); server.send(204); }

void applyAll(){
  digitalWrite(LED_ROJO,     st==ROJO);
  digitalWrite(LED_AMARILLO, st==AMARILLO);
  digitalWrite(LED_VERDE,    st==VERDE);
  if(st==ROJO) setOpen(false); else setOpen(true);
  if(lcd_on){
    lcd.setCursor(0,0); lcd.print(pad16("Sem: "+stText()));
    String t = nowIso(); String hhmm = (t.length()>=19)? t.substring(11,19):"--:--:--";
    lcd.setCursor(0,1); lcd.print(pad16("Hora: "+hhmm));
  }
}

// === API ===
void api_state(){
  String j="{\"running\":"; j+=(running?"true":"false");
  j+=",\"stage\":\""+stText()+"\"";
  j+=",\"time\":\""+nowIso()+"\"";
  j+=",\"servos\":\""; j+=(opened? "OPEN" : "CLOSE"); j+="\"";
  j+=",\"lcd\":"; j+=(lcd_on?"true":"false"); j+="}";
  sendJSON(j);
}
void api_start(){ running=true; t0=millis(); applyAll(); sendOK(); }
void api_stop(){ running=false; digitalWrite(LED_ROJO,0); digitalWrite(LED_AMARILLO,0); digitalWrite(LED_VERDE,0); setOpen(false); sendOK(); }
void api_open(){ setOpen(true); sendOK(); }
void api_close(){ setOpen(false); sendOK(); }
void api_settime(){
  if(!server.hasArg("iso")) return sendBad("Missing iso");
  DateTime dt; if(!parseISO(server.arg("iso"), dt)) return sendBad("Bad iso");
  if(!rtc_ok) return sendBad("RTC not ready");
  rtc.adjust(dt); applyAll(); sendOK();
}
void api_lcd_clear(){ lcd.clear(); sendOK(); }
void api_lcd_backlight(){
  bool on = server.arg("on")=="1" || server.arg("on")=="true";
  lcd_on = on;
  if(on) lcd.backlight(); else lcd.noBacklight();
  sendOK();
}
void api_lcd_print(){
  int row = server.hasArg("row")? server.arg("row").toInt():0;
  if(row<0) row=0; if(row>1) row=1;
  String text = server.hasArg("text")? server.arg("text"):"";
  lcd.setCursor(0,row); lcd.print(pad16(text));
  sendOK();
}
void api_lcd_cursor(){
  int row = server.hasArg("row")? server.arg("row").toInt():0;
  int col = server.hasArg("col")? server.arg("col").toInt():0;
  if(row<0) row=0; if(row>1) row=1;
  if(col<0) col=0; if(col>15) col=15;
  lcd.setCursor(col,row); sendOK();
}

void setup(){
  Serial.begin(115200);
  pinMode(LED_ROJO,OUTPUT); pinMode(LED_AMARILLO,OUTPUT); pinMode(LED_VERDE,OUTPUT);
  idleServoPins();

  Wire.begin(21,22);
  lcd.init(); lcd.backlight(); lcd.clear();
  lcd.setCursor(0,0); lcd.print("ESP32 Semaforos");
  lcd.setCursor(0,1); lcd.print("Iniciando...    ");

  rtc_ok = rtc.begin();
  if(rtc_ok && rtc.lostPower()){ rtc.adjust(DateTime(F(__DATE__),F(__TIME__))); }

  s1.setPeriodHertz(50); s2.setPeriodHertz(50);
  servo1Angle = A_CLOSE; servo2Angle = A_CLOSE; opened=false;
  servosAttached=false;

  WiFi.mode(WIFI_STA); WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi"); for(int i=0;i<60 && WiFi.status()!=WL_CONNECTED;i++){ delay(500); Serial.print("."); }
  Serial.println(); Serial.print("IP: "); Serial.println(WiFi.localIP());
  lcd.clear(); lcd.setCursor(0,0); lcd.print("IP: "); lcd.print(WiFi.localIP().toString().c_str());

  // Rutas
  server.on("/", HTTP_GET, [](){ addCORS(); server.send(200,"text/plain","ESP32 OK"); });

  server.on("/api/state", HTTP_GET, api_state);
  server.on("/api/start", HTTP_GET, api_start);
  server.on("/api/stop",  HTTP_GET, api_stop);
  server.on("/api/open",  HTTP_GET, api_open);
  server.on("/api/close", HTTP_GET, api_close);
  server.on("/api/settime", HTTP_GET, api_settime);

  server.on("/api/lcd/clear",     HTTP_GET, api_lcd_clear);
  server.on("/api/lcd/backlight", HTTP_GET, api_lcd_backlight);
  server.on("/api/lcd/print",     HTTP_GET, api_lcd_print);
  server.on("/api/lcd/cursor",    HTTP_GET, api_lcd_cursor);

  server.onNotFound([](){ addCORS(); server.send(404,"text/plain","Not found"); });
  server.on("/", HTTP_OPTIONS, handle_options);

  server.begin();

  st=ROJO; running=false; t0=millis(); applyAll();
}

void loop(){
  server.handleClient();
  if(running && (millis()-t0 >= dur())){
    st = (st==ROJO)?VERDE:(st==VERDE?AMARILLO:ROJO);
    t0 = millis(); applyAll();
  }
  static uint32_t last=0; if(millis()-last>500){ last=millis(); applyAll(); }
}

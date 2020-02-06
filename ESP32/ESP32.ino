#include"WiFi.h"
#include"WiFiUdp.h"
#include<math.h>
#include<stdio.h>
#include<stdlib.h> 


#define sgn(x)  (x > 0) ? 1 : ((x < 0) ? -1 : 0)
#define WAIT_TIME 50

const bool debug = false;

const char* ssid = "Raspi_gmg";
const char* pass = "tossacoin";

const char* host = "192.168.4.1";
const int port = 44444;

const float AMPLITUDE = 1;
const float FS = round(1000 / WAIT_TIME);

int an = 0;

int count = 0;
float anomaly;
float sig;
float season;
float trend;
float trend_gradient;
float noise;

enum trendStateMachine {DOWN = -1, UP = +1};
enum trendStateMachine trendState = UP;


WiFiUDP udp;

void _check_read_udp(uint8_t buffer[])
{
  if (udp.read(buffer, 50) > 0)
  {
    Serial.print("Recieved from Pi : ");
    Serial.print((char *) buffer);
    Serial.print(" At ");
    Serial.println(millis());
  }
}

float generateTrend(float trend)
{
  float modifier = ((float)random(100))/500.0;
  float change = random(100);
  if (debug==true)
  {
    Serial.println(" ");
    Serial.print("change ");
    Serial.println(change);
  }
  if (change > 90)
  {
    modifier = ((float)random(100))/200.0;
    switch (trendState)
    {
      case UP:
        trendState = DOWN;
        if (debug==true)
        {
          Serial.println(" ");
          Serial.print("changed to ");
          Serial.println(DOWN);
        }
        break;
      case DOWN:
        trendState = UP; 
        if (debug==true)   
        {
          Serial.println(" ");
          Serial.print("changed to ");
          Serial.println(UP);
        }    
        break;

    }
    
    trend_gradient = trendState * modifier;
//    if (trend_gradient == 0)
//      trend_gradient = -1 * modifier;

    
  }
  if (debug==true)   
  {
    Serial.print("Gradient : ");
    Serial.println(trend_gradient);
    Serial.print("modifier : ");
    Serial.println(modifier);
  }
  return trend + trend_gradient;
  
}

void setup() {
 // put your setup code here, to run once:

  
  Serial.begin(115200);

  randomSeed(5);
  delay(10);
  Serial.println("\n");
  Serial.print("Trend State: ");
  Serial.println(trendState);
  trend = 0;
  trend_gradient = 0.1 / FS;
  Serial.print("Trend State: ");
  Serial.println(trendState);
  Serial.print(UP);
  Serial.print(", ");
  Serial.println(DOWN);
  int n = WiFi.scanNetworks();

  WiFi.begin(ssid, pass);
  Serial.print("Establishing connection to ");
  Serial.print(ssid);
  Serial.println("...");
  int i=0;
  while (WiFi.status() != WL_CONNECTED){
    delay(1000);
    Serial.print(++i); Serial.print(" ");
  }
  Serial.println("\n");
  Serial.println("Connected!!");
  Serial.println("Current IP address is: ");
  Serial.println(WiFi.localIP());
  udp.begin(port);
  Serial.println("\n\n\n");

  delay(1000);
}

void loop() {
  bool rd = false;
  anomaly = (float) random(1000);
  noise = (float) random(100)/700;
  season = sgn(sin(count / FS * M_PI));
  trend = generateTrend(trend);
  // need to fix the trend
  sig = season + trend + noise;
  if (anomaly > 970)
  {
    sig += (anomaly / 1000);
    an = 1;
  }

  char part1[10];
  uint8_t buffer[50];
  dtostrf(sig, 5, 2, part1);
  String string1 = part1;
  String dat = string1 + "," + millis() + "," + an;
  Serial.print("sig: ");
  Serial.print(sig);
  Serial.print(" at ");
  Serial.println(millis());
  udp.beginPacket(host, port);
  udp.print(dat);
  udp.endPacket();
  int sentmillis = millis();
  memset(buffer, 0, 50);
  udp.parsePacket();
  
//  if (udp.read(buffer, 50) > 0)
//  {
//    Serial.print("Recieved from Pi : ");
//    Serial.print((char *) buffer);
//    Serial.print(" At ");
//    Serial.println(millis());
//  }
  while(true)
  { 
    _check_read_udp(buffer);
    
    if ((millis() - sentmillis) > WAIT_TIME){
      break; 
    }
  }
  count += 1;
  an = 0;
  
}

#include <CmdMessenger.h>
#include <EEPROM.h>
#include <Wire.h>
#include <LM75.h>

struct Config {
  boolean lm75;
  boolean thermistor;
};

enum {log_message, foo_message,};

static const int led = 13;
static const int temp = 1;
static const int configAddress = 0;
LM75 lm75;
Config config;

CmdMessenger c = CmdMessenger(Serial,',',';','/');

// the setup routine runs once when you press reset:
void setup() {
  Wire.begin();
  Serial.begin(9600);
  attach_callbacks();

  log("Starting node....");

  // read config from EEPROM
  EEPROM.get(configAddress, config);
  log(config.lm75?"lm75":"no lm75");
  log(config.thermistor?"thermistor":"no thermistor");

  if (config.thermistor) {
    // setup thermistor
    // nada
    }

  if (config.lm75) {
    // setup i2c
    // nada
  }

  // initialize the digital pin as an output.
  pinMode(led, OUTPUT);

  log("Init done");
}

// the loop routine runs over and over again forever:
void loop() {
  digitalWrite(led, HIGH);   // turn the LED on (HIGH is the voltage level)
  delay(2500);               // wait for a second
  digitalWrite(led, LOW);    // turn the LED off by making the voltage LOW
  delay(2500);               // wait for a second

  //TODO:
  //c.feedinSerialData();
  if (config.thermistor) {
    int value = analogRead(A0);
    float temp = temperature(resistance(value));
    char buf[100];
    dtostrf(temp, 5, 2, buf);

    log("temp(thermistor): ");
    log(buf);
  }

  if (config.lm75) {
    float temp = lm75.temp();
    char buf[100];
    dtostrf(temp, 5, 2, buf);

    log("temp(lm75): ");
    log(buf);
  }
}

float resistance(int a) {
  return (float)(1023-a)*10000/a;
}

float temperature(float res) {
  return 1/(log(res/10000)/3975+1/298.15) - 273.15;
}

void attach_callbacks() {
  c.attach(nada);
}

void nada() {

}

void log(const char* caaa) {
  c.sendCmd(log_message, caaa);
}

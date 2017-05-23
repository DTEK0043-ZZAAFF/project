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


// TODO: should be in header file?
/**
 * Wrap sendCmd. Internally PyCmdMessenger use Stream class and supports
 * formatting automatically!
 */
template < class T > inline void logger(T caaa) {
  c.sendCmd(log_message, caaa);
}

// the setup routine runs once when you press reset:
void setup() {
  Wire.begin();
  Serial.begin(9600);
  attach_callbacks();

  logger("Starting node....");

  // read config from EEPROM
  EEPROM.get(configAddress, config);
  logger(config.lm75?"lm75":"no lm75");
  logger(config.thermistor?"thermistor":"no thermistor");

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

  logger("Init done");
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

    logger("temp(thermistor): ");
    logger(temp);
  }

  if (config.lm75) {
    float temp = lm75.temp();

    logger("temp(lm75): ");
    logger(temp);
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

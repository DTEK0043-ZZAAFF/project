#include <CmdMessenger.h>
#include <Wire.h>
#include <LM75.h>

enum {send_log, send_temp, send_pir, request_lm75, send_mock};

static const int led = 13;
static const int temp = 1;
static const int configAddress = 0;
static boolean enable_lm75 = false;

LM75 lm75;
CmdMessenger c = CmdMessenger(Serial,',',';','/');

/**
 * Wrap sendCmd. Internally PyCmdMessenger use Stream class and supports
 * formatting automatically!
 */
template < class T > inline void logger(T data) {
  c.sendCmd(send_log, data);
}

// the setup routine runs once when you press reset:
void setup() {
  Wire.begin();
  Serial.begin(9600);
  attach_callbacks();

  logger("Starting node....");

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

  c.feedinSerialData();

  if (!enable_lm75) {
    int value = analogRead(A0);
    float temp = temperature(resistance(value));
    c.sendBinCmd(send_temp, temp);
  } else {
    float temp = lm75.temp();
    c.sendBinCmd(send_temp, temp);
  }
}

// helper functions
float resistance(int a) {
  return (float)(1023-a)*10000/a;
}

float temperature(float res) {
  return 1/(log(res/10000)/3975+1/298.15) - 273.15;
}

//callbacks
void attach_callbacks() {
  c.attach(request_lm75, on_request_lm75);
  c.attach(send_mock, on_send_mock);
  c.attach(on_unknown_request);
}

void on_unknown_request() {
  logger("Got unknown request!");
}

void on_request_lm75() {
  enable_lm75 = true;
  logger("Turned on lm75");
}

void on_send_mock() {
  logger("on_send_mock");
  logger(c.readStringArg());
}

/**
 * Arduino code for DTEK0043 project
 *
 * @author: Janne Kujanpää
 * @version: 0.0.1
 */

 /*
Copyright (c) 2017 Janne Kujanpää

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

/*
 * Licenses for used libraries
 * Arduino libraries: LGPL
 * AVR libc: http://www.nongnu.org/avr-libc/LICENSE.txt Modified BSD
 * CmdMessenger: https://github.com/thijse/Arduino-CmdMessenger MIT
 * LM75: https://github.com/thefekete/LM75 GPLv3
 */

#include <CmdMessenger.h>
#include <Wire.h>
#include <LM75.h>
/** This enum stores message types for CmdMessenger
 *
 * Types must be in same order here and in gateway code.
 * Enum value is send as message identier and gateway code uses that value
 * when parsing the message
 */
enum {send_log,
  send_temp,
  send_pir,
  request_lm75,
  send_mock,
  request_uid_status,
  send_uid_status,
  request_pir,
  force_unlock,};

// used PINs
static const int ledPin = 13;
static const int pirPin = 2;
static const int thermPin = A0;

// global config if features are enabled
static boolean enable_lm75 = false;
static boolean enable_pir = false;

// multiple state values
static int prev_pir_state = LOW;
static boolean unlockRequestPending = false;
static unsigned long unlockRequestTime;
static const int unlockRequestTimeout = 10000;
static boolean lockOpen = false;
static unsigned long lockOpenTime;
static const int lockOpenTimeout = 5000;
static unsigned long lastMeasure = 0;

// hardware abstractions
LM75 lm75;
CmdMessenger c = CmdMessenger(Serial,',',';','/');

/** Wrap sendCmd. Message can be any type supported by `Stream` class
 *
 * @param message to send.
 */
template < class T > inline void logger(T data) {
  c.sendCmd(send_log, data);
}

// the setup routine runs once when you press reset:
void setup() {
  Wire.begin();
  Serial.begin(9600);
  attach_callbacks();
  delay(100);

  logger("Starting setup()");
  pinMode(ledPin, OUTPUT);
  logger("setup() done");
}

// the loop routine runs over and over again forever:
void loop() {
  if (unlockRequestPending) {
    for (int i=1;i<=5;i++) {
      digitalWrite(ledPin, HIGH);   // turn the LED on (HIGH is the voltage level)
      delay(50);
      digitalWrite(ledPin, LOW);    // turn the LED off by making the voltage LOW
      delay(50);
    }
  } else {
    delay(500);
  }

  // read CmdMessenger. Callback functions called there are messages in Serial FIFO
  c.feedinSerialData();

  // TODO: measure only when requested?
  // once per 30 seconds send temperature measurement to gateway
  if (lastMeasure + 30000 < millis()) {
    lastMeasure = millis();
    if (!enable_lm75) {
      int value = analogRead(thermPin);
      float temp = temperature(resistance(value));
      c.sendBinCmd(send_temp, temp);
    } else {
      float temp = lm75.temp();
      c.sendBinCmd(send_temp, temp);
    }
  }

  if (enable_pir) {
    int val = digitalRead(pirPin);
    if (prev_pir_state == LOW && val == HIGH) {
      // rising edge, movement detected. send message to gateway
      c.sendCmd(send_pir);
      prev_pir_state = val;
    } else if (prev_pir_state == HIGH && val == LOW) {
      // falling edge
      prev_pir_state = val;
    }
  }

  // timeout for pending unlock request
  if (unlockRequestPending && (millis() > unlockRequestTime + unlockRequestTimeout)) {
    unlockRequestPending = false;
    logger("WARNING: unlock request timeouted");
  }

  // close lock after predefined timeout
  if (lockOpen && (millis() > lockOpenTime + lockOpenTimeout)) {
    // timeout open lock
    digitalWrite(ledPin, LOW);
    lockOpen = false;
    logger("INFO: door locked");
  }
}

/** helper function for thermistor
 */
float resistance(int a) {
  return (float)(1023-a)*10000/a;
}

/** helper function for thermistor
 */
float temperature(float res) {
  return 1/(log(res/10000)/3975+1/298.15) - 273.15;
}

/** Registers all CmdMessenger callbacks
 */
void attach_callbacks() {
  c.attach(request_lm75, on_request_lm75);
  c.attach(request_pir, on_request_pir);
  c.attach(send_mock, on_send_mock);
  c.attach(send_uid_status, on_send_uid_status);
  c.attach(force_unlock, on_force_unlock);
  c.attach(on_unknown_request);
}

/** Callback function: called when unknown or message type with no callback is
 * received from gateway
 */
void on_unknown_request() {
  logger("ERROR: Received unknown request!");
}

/** Callback function: called when gateway requests to use LM75 sensor
 */
void on_request_lm75() {
  enable_lm75 = c.readBinArg<bool>();
}

/** Callback function: called when gateway requests to enable PIR measurement
 */
void on_request_pir() {
  enable_pir = c.readBinArg<bool>();
}

/** Callback function: called when gateway sends mockup message
 *
 * This is for mocking NFC reader and PIR level changes
 */
void on_send_mock() {
  // note UIDs usually have fixed length
  char* uid = c.readStringArg();
  char* cmd = strtok(uid, ":");
  char* msg = strtok(NULL, "");

  if (strcasecmp(cmd, "mock") == 0) {
    if (!unlockRequestPending) {
      //c.sendBinCmd(request_uid_status, uid);
      c.sendCmd(request_uid_status, msg);
      unlockRequestPending = true;
      unlockRequestTime = millis();
      logger("INFO: trying unlock from mock");
    } else {
      logger("WARNING: RFID read ignored, already pending");
    }
    return;
  }

  if (strcasecmp(cmd, "piru") == 0) {
    if (prev_pir_state == LOW) {
      c.sendCmd(send_pir);
      prev_pir_state = HIGH;
    }
    return;
  }

  if (strcasecmp(cmd, "pird") == 0) {
    if (prev_pir_state == HIGH) {
      prev_pir_state = LOW;
    }
    return;
  }
}

/** Callback function: called when gateway tell if requested UID has rights to unlock door
 */
void on_send_uid_status() {
  boolean unlock = c.readBinArg<bool>();
  unlockRequestPending = false;
  if (unlock) {
    lockOpen = true;
    lockOpenTime = millis();
    logger("INFO: door open");
    digitalWrite(ledPin, HIGH);
  } else {
    logger("WARNING: unlisted uid!");
    lockOpen = false; // just lock it
  }
}

/** Callback function: called when gateway requests to unlock door
 */
void on_force_unlock() {
  unlockRequestPending = false;
  lockOpen = true;
  lockOpenTime = millis();
  logger("INFO: door open");
  digitalWrite(ledPin, HIGH);
}

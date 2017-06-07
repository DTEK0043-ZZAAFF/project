#include <CmdMessenger.h>
#include <Wire.h>
#include <LM75.h>

enum {send_log,
  send_temp,
  send_pir,
  request_lm75,
  send_mock,
  request_uid_status,
  send_uid_status,
  request_pir,
  force_unlock,};

static const int ledPin = 13;
static const int pirPin = 2;
static const int thermPin = A0;
static boolean enable_lm75 = false;
static boolean enable_pir = false;
static int prev_pir_state = LOW;
static boolean unlockRequestPending = false;
static unsigned long unlockRequestTime;
static const int unlockRequestTimeout = 10000;
static boolean lockOpen = false;
static unsigned long lockOpenTime;
static const int lockOpenTimeout = 5000;
static unsigned long lastMeasure = 0;



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
}

  // feature. Give some tome to settle before reading Serial
  c.feedinSerialData();

  // TODO: measure only when requested?
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
      // rising edge
      c.sendCmd(send_pir);
      prev_pir_state = val;
    } else if (prev_pir_state == HIGH && val == LOW) {
      // falling edge
      prev_pir_state = val;
    }
  }

  if (unlockRequestPending && (millis() > unlockRequestTime + unlockRequestTimeout)) {
    // timeout for pending unlock request
    unlockRequestPending = false;
    logger("WARNING: unlock request timeouted");
  }

  if (lockOpen && (millis() > lockOpenTime + lockOpenTimeout)) {
    // timeout open lock
    digitalWrite(ledPin, LOW);
    lockOpen = false;
    logger("INFO: door locked");
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
  c.attach(request_pir, on_request_pir);
  c.attach(send_mock, on_send_mock);
  c.attach(send_uid_status, on_send_uid_status);
  c.attach(force_unlock, on_force_unlock);
  c.attach(on_unknown_request);
}

void on_unknown_request() {
  logger("ERROR: Received unknown request!");
}

void on_request_lm75() {
  enable_lm75 = c.readBinArg<bool>();
}

void on_request_pir() {
  enable_pir = c.readBinArg<bool>();
}

/*
 * This is for mocking NFC reader because we did not have
 * hardware access. Real NFC readers have I2C bus and
 * current libraries uses various ways to get UID
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

void on_force_unlock() {
  unlockRequestPending = false;
  lockOpen = true;
  lockOpenTime = millis();
  logger("INFO: door open");
  digitalWrite(ledPin, HIGH);
}

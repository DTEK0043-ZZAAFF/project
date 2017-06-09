# Install project locally
## Clone project files
```
mkdir -p src/dtek0043
cd src/dtek0043

git clone https://github.com/DTEK0043-ZZAAFF/project
```

## Install libraries for Arduino
```
mkdir -p ~/Arduino/libraries
cd ~/Arduino/libraries/
git clone https://github.com/thefekete/LM75
git clone https://github.com/thijse/Arduino-CmdMessenger
mv Arduino-CmdMessenger/ ArduinoCmdMessenger/
# Legacy Arduino IDE stops working if it libraries it detect contains dash
```

## Run Arduino node
1) Open Arduino IDE
2) Select `File => Open` and navigate to `~/dtek0043/project/iot_project/iot_project.ino`
3) Upload sketch

## Install backend
```
cd ~/src/dtek0043
git clone https://github.com/DTEK0043-ZZAAFF/backend
mvn spring-boot:run
```
Backend process is now running in http://localhost:8080
Note: you should create own application.properties file in root directory of backend. See https://github.com/DTEK0043-ZZAAFF/backend/blob/master/src/main/resources/application.properties
for reference.

Installation and running local MQTT server is out of scope for this project. Just download
MQTT server and run. I personally used HiveMQ

## Install libraries and run gateway
* `pip install --user paho-mqtt`
* gateway is now ready to run with command `python gateway.py ...`
  E.g. `python --myrest http://localhost:8080 --verbosity degub --mymqtt tcp://localhost:1883 --lm75 --name foo /dev/ttyACM0`
* Everything should be working now. Something is available in http://localhost:8080/

## Notes for development process notes
* Close all serial connections before trying to upload new sketch. `CTRL+C` stops python process.

# Randoms
## My personal recommendation
PlatformIO with atom is worth of trying.

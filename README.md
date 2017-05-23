# Usage with Arduino

1) Install dependencies:
 * https://github.com/thefekete/LM75
 * https://github.com/thijse/Arduino-CmdMessenger
   * This library might require patch included in extras folder
   * TODO: test and document

2) Open iot-project/iot-project.ino with Arduino IDE

3) Configure local Arduino node
 * Upload and run once TODO.ino to setup EEPROM

4) Test
 * Upload into Arduino
 * Run TODO.py

# Usage with platformIO
1) Install dependencies into Arduino IDE
   * Arduino-CmdMessenger requires patch mentioned in Arduino notes because library is shipped with depencies required for example codes.
2) Build/Run

# Gateway
Install python 2.7 and pySerial. Then just run foo.py

# Notes
## Fixed version of PyCmdMessenger
Port to 2.7 was broken. Fixed version: https://github.com/DTEK0043-ZZAAFF/PyCmdMessenger/tree/python27

To simplify code process I have imported copy of the library into this repo

# TODO
Write configurator

# Usage with Arduino

1) Install dependencies:
 * https://github.com/thefekete/LM75
 * https://github.com/thijse/Arduino-CmdMessenger
   * This library might require patch included in extras folder
   * TODO: test and document

2) Open iot-project/iot-project.ino with Arduino IDE

3) Test
 * Upload into Arduino
 * install python dependencies
   * `pip install pyserial`
   * `pip install requests`
 * Run gateway.py

# Usage with platformIO
1) Install dependencies into Arduino IDE
   * Arduino-CmdMessenger requires patch mentioned in Arduino notes because library is shipped with dependencies required for example codes.
2) Build/Run

# Gateway
TBD

# Notes
* Google docs document: TBD
* Notes for lab usage: https://github.com/DTEK0043-ZZAAFF/project/blob/master/Notes-for-k127.md

## Fixed version of PyCmdMessenger
Port to 2.7 was broken. Fixed version: https://github.com/DTEK0043-ZZAAFF/PyCmdMessenger/tree/python27

To simplify code process I have imported copy of the library into this repo

# TODO
* gateway.pl: Write HTTP poll to monitor unlock requests initiated from backend
* Use AWS IoT / some other backend / at least send data to AWS IoT for later use

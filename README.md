# Description
This repository contains Arduino and gateway code for DTEK0043 course project.
Backend code is available in https://github.com/DTEK0043-ZZAAFF/backend

# License
See source files for their respective license. Almost all is MIT licensed

All other files including documentation files: All rights reserved

# Notes for Arduino code
1) Install dependencies:
 * https://github.com/thefekete/LM75
 * https://github.com/thijse/Arduino-CmdMessenger

2) Open iot-project/iot-project.ino with Arduino IDE

3) Test
 * Upload into Arduino

# Notes for python code
 * install missing python dependencies
   * `pip install pyserial`
   * `pip install requests`
   * `pip install paho-mqtt`
   * `pip install pyfiglet` used by external script
 * Run gateway.py with valid set of arguments. Execute `python gateway.py --help`
   to see list of arguments

# Usage with platformIO
Open cloned directory as document. If using Arduino-CmdMessenger library from
Arduino's library directory Arduino-CmdMessenger/library.json dependencies must
be removed.

# Notes
* Notes for lab room usage: https://github.com/DTEK0043-ZZAAFF/project/blob/master/Notes-for-k127.md

## Fixed version of PyCmdMessenger
Port to 2.7 was broken. Fixed version: https://github.com/DTEK0043-ZZAAFF/PyCmdMessenger/tree/python27

To simplify code process I have imported copy of the library into this repo

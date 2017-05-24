# Install project locally
## Clone project files
```
mkdir -p src/dtek0043
cd src/dtek0043

git clone https://github.com/DTEK0043-ZZAAFF/project
```

## Install new Arduino IDE

Download newest 64-bit version for linux
```
cd ~
mkdir opt
cd opt
tar -axf ~/Downloads/arduino-1.8.1-linux64.tar.xz
cd
ln -s /lib64/libncurses.so.5 libtinfo.so.5
~/opt/arduino-1.8.1/arduino
```

Why to install new Arduino IDE?
* Preinstalled Arduino IDE has been released in 2013. Multiple builtin libraries have been updated. E.g. EEPROM.get() has been added after 1.0.5 release.

Why symlink?
* Ask admin(s)

## Install libraries
```
mkdir -p ~/Arduino/libraries
cd ~/Arduino/libraries/ or fucking
git clone https://github.com/thefekete/LM75
git clone https://github.com/thijse/Arduino-CmdMessenger
mv Arduino-CmdMessenger/ ArduinoCmdMessenger/ 
# Legacy Arduino IDE stops working if it libraries it detect contains dash
```

## Run project
1) Run Arduino IDE we just installed: e.g. `~/opt/arduino-1.8.1/arduino`
2) Select `File => Open` and navigate to `~/dtek0043/project/iot_project/iot_project.ino`
3) Upload sketch
4) Open new Terminal
   * `~/opt/arduino-1.8.1/arduino`
   * `python foo.py`
   
## Development process notes
* Close all serial connections before trying to upload new sketch. `CTRL+C` stops python process.

# Random Notes
## Installed versions
* Arduino 1.0.5
* Python 2.7.13
* Slackware 14.1

# Random
## My personal recommendation
Stop using old Arduino IDE and/or try PlatformIO. If you need old legacy version consider saving sketches and libraries in `~/sketchbook` and for newer version in `~/Arduino`.

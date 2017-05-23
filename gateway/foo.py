import sys
from datetime import datetime
import time
import PyCmdMessenger

arduino = PyCmdMessenger.ArduinoBoard(sys.argv[1],baud_rate=9600)

commands = [["log", "s"],
["foo", ""]]

c = PyCmdMessenger.CmdMessenger(arduino,commands)

while True:
    message = c.receive()
    if message == None:
        print("{0}: {1}".format(datetime.now().isoformat(), "No message!"))
    if message != None and message[0] is "log":
        print("{0}: {1}".format(datetime.now().isoformat(),message[1][0]))
    #time.sleep(5)

from __future__ import print_function
import sys
from datetime import datetime
import time
import requests
import json

import PyCmdMessenger

arduino_port = sys.argv[1]
api_url = sys.argv[2]
node_name = sys.argv[3]

# Usage: c:\Python27\python.exe foo.py COM5 http://localhost:8080/api/v1a bar aa
# c:\Python27\python.exe foo.py <com port> <api address> <node name> <enter some argument to turn of lm75 logging>
def main():
    online = False
    lm75 = False
    if len(sys.argv) > 4:
        lm75 = True


    # init REST connection
    node_url = init_rest()

    if node_url != None:
        print("Node URL: " + node_url)
        online = True

    # init arduino and CmdMessenger
    arduino = PyCmdMessenger.ArduinoBoard(arduino_port,baud_rate=9600)

    commands = [["send_log", "s"],
                ["send_temp", "d"],
                ["send_pir", ""],
                ["request_lm75", ""]]

    c = PyCmdMessenger.CmdMessenger(arduino,commands)

    # turn on lm75 temperature logging when requested
    if lm75:
        c.send("request_lm75")

    while True:
        message = c.receive()
        if message == None:
            print("{0}: {1}".format(datetime.now().isoformat(), "No message!"))
        else:
            message_type = message[0]
            msg = message[1][0]
            if message_type is "send_log":
                print("{0}: {1}".format(datetime.now().isoformat(), msg))
            elif message_type is "send_temp":
                print("{0}: Temperature: {1}".format(datetime.now().isoformat(), msg))
                online and requests.post(api_url + "/temperatures", json={"node": node_url, "value": msg})
            elif message_type is "send_pir":
                print("{0}: PIR detection!".format(datetime.now().isoformat()))
                online and requests.post(api_url + "/pirs", json={"node": node_url})

def init_rest():
    r = requests.get(api_url)
    if r.status_code != 200:
        print("ERROR: check API URL")
        return None

    address = api_url + "/nodes/search/findByName?name=" + node_name
    r = requests.get(address)
    if r.status_code == 404:
        print("WARNING: node not found, creating!")
        r = requests.post(api_url + "/nodes", json={"name": "node_name"})
        if r.status_code == 201:
            json_data = json.loads(r.text)
            return json_data["_links"]["self"]["href"]
        else:
            print(r.status_code)
            print(r.text)
            sys.exit("failed")
    else:
        json_data = json.loads(r.text)
        return json_data["_links"]["self"]["href"]

if __name__ == "__main__":
    main()

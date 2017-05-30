from __future__ import print_function
import argparse
import asyncore
import json
import logging
import requests
import string
import sys
import threading
import traceback

import PyCmdMessenger
import MsgServer

# simple command line parsing
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbosity", type=int, default=0, choices=[0, 1, 2],
                    help="increase output verbosity")
parser.add_argument("--online", type=str, metavar="PROTO://ADDRESS:PORT",
                    help="Enable online storage")
parser.add_argument("--lm75", action="store_true", help="Use LM75 sensor")
parser.add_argument("--name", default="default_node", metavar="NAME",
                    help="Name of the node")
parser.add_argument("com", default="/dev/ttyACM0", metavar="COM_PORT",
                    help="COM port to use")
args = parser.parse_args()

# setup variables
arduino_port = args.com
if args.online == None:
    api_url = None
    online = False
else:
    api_url = args.online
    online = True
node_name = args.name

# init arduino and CmdMessenger
arduino = PyCmdMessenger.ArduinoBoard(arduino_port, baud_rate=9600)

commands = [["send_log", "s"],
            ["send_temp", "d"],
            ["send_pir", None],
            ["request_lm75", ""],
            ["send_mock", "s"],
            ["request_uid_status", "s"],
            ["send_uid_status", "?"]]

c = PyCmdMessenger.CmdMessenger(arduino, commands)

# Usage: c:\Python27\python.exe foo.py COM5 http://localhost:8080/api/v1a bar aa
# python.exe foo.py <com port> <api address> <node name> <arg to enable lm75>
def main():
    global c
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("main")
    nodeLogger = logging.getLogger("Arduino")
    online = False
    lm75 = False
    if len(sys.argv) > 4:
        lm75 = True

    # init internal command server
    init_msg_server()

    # init REST connection
    if online:
        node_url = init_rest()

        if node_url != None:
            logger.info("Node URL: %s", node_url)
            online = True

    # turn on lm75 temperature logging when requested
    if lm75:
        c.send("request_lm75")

    while True:
        try:
            message = c.receive()
        except Exception as e:
            message = None
            logger.error(traceback.format_exc())

        if message == None:
            pass
        else:
            message_type = message[0]
            msg = message[1][0]
            if message_type is "send_log":
                nodeLogger.debug(msg)
            elif message_type is "send_temp":
                logger.debug("temp: %s", msg)
                online and requests.post(api_url + "/temperatures",
                                         json={"node": node_url, "value": msg})
            elif message_type is "send_pir":
                logger.debug("PIR detection!")
                online and requests.post(api_url + "/pirs",
                                         json={"node": node_url})
            elif message_type is "request_uid_status":
                logger.debug("uid status request: %s", msg)
                online and requests.get(api_url + "TODO",
                                       json={"node": node_url})
                # TODO: we need result
            else:
                logger.warn("Unknown message_type: %s", message_type)
                logger.warn("with message: %s", message[1])

def init_rest():
    r = requests.get(api_url)
    if r.status_code != 200:
        logger.error("check API URL")
        return None

    address = api_url + "/nodes/search/findByName?name=" + node_name
    r = requests.get(address)
    if r.status_code == 404:
        logger.warn("Node not found, creating!")
        r = requests.post(api_url + "/nodes", json={"name": "node_name"})
        if r.status_code == 201:
            json_data = json.loads(r.text)
            return json_data["_links"]["self"]["href"]
        else:
            logger.debug("%s %s", r.status_code, r.text)
            sys.exit("failed")
    else:
        json_data = json.loads(r.text)
        return json_data["_links"]["self"]["href"]

def init_msg_server():
    logging.debug('Serving on localhost:5050')
    server = MsgServer.MsgServer('localhost', 5050, c.send)
    loop_thread = threading.Thread(target=asyncore.loop, name="Asyncore Loop")
    loop_thread.daemon = True
    loop_thread.start()



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()

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
import CmdEvents

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

restSuffix = "/api/v1"
unlockSuffix = "/api/v2"

# init arduino and CmdMessenger
arduino = PyCmdMessenger.ArduinoBoard(arduino_port, baud_rate=9600)

commands = [["send_log", "s"],
            ["send_temp", "d"],
            ["send_pir", ""],   # TODO: bug here, does not allow None
            ["request_lm75", ""],
            ["send_mock", "s"],
            ["request_uid_status", "s"],
            ["send_uid_status", "?"]]

c = PyCmdMessenger.CmdMessenger(arduino, commands)
logger = logging.getLogger("main")
nodeLogger = logging.getLogger("Arduino")

def main():
    global c, online
    logging.basicConfig(level=logging.DEBUG)

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
        else:
            logger.warn("Failed to initialize REST")
            online = False

    # turn on lm75 temperature logging when requested
    if lm75:
        c.send("request_lm75")

    # prepate event handler
    event_handler = CmdEvents.CmdEvents(c)
    event_handler.addListener("send_log", on_send_log)
    event_handler.addListener("send_temp", on_send_temp)
    event_handler.addListener("send_pir", on_send_pir)
    event_handler.addListener("request_uid_status", on_request_uid_status)
    # start event handler (blocks)
    event_handler.run()

# callback
def on_send_log(msg):
    nodeLogger.debug(msg)

def on_send_temp(msg):
    logger.debug("temp: %s", msg)
    online and requests.post(api_url + restSuffix + "/temperatures",
                             json={"node": node_url, "value": msg})

def on_send_pir(msg):
    logger.debug("PIR detection!")
    online and requests.post(api_url + restSuffix + "/pirs",
                             json={"node": node_url})

def on_request_uid_status(msg):
    logger.debug("uid status request: %s", msg)
    if online:
        r = requests.get(api_url + unlockSuffix + "/checkpermission/"
                     + string.split(node_url, "/")[-1] + "/" + msg)
        if r.status_code is 200:
            c.send("send_uid_status", True)
        else:
            c.send("send_uid_status", False)

# helpers
def init_rest():
    r = requests.get(api_url + restSuffix)
    if r.status_code != 200:
        logger.error("check API URL")
        return None

    address = api_url + restSuffix + "/nodes/search/findByName?name=" + node_name
    r = requests.get(address)
    if r.status_code == 404:
        logger.warn("Node not found, creating!")
        r = requests.post(api_url + restSuffix + "/nodes", json={"name": "node_name"})
        if r.status_code == 201:
            json_data = json.loads(r.text)
            return json_data["_links"]["self"]["href"]
        else:
            logger.debug("%s %s", r.status_code, r.text)
            sys.exit("failed")
    else:
        logger.debug("REST OK")
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

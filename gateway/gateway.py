from __future__ import print_function
import argparse
import asyncore
import json
import logging
import requests
import string
import sys
import threading
import time

import PyCmdMessenger
import MsgServer
import CmdEvents

commands = [["send_log", "s"],
            ["send_temp", "d"],
            ["send_pir", ""],   # TODO: bug here, does not allow None
            ["request_lm75", "?"],
            ["send_mock", "s"],
            ["request_uid_status", "s"],
            ["send_uid_status", "?"],
            ["request_pir", "?"]]

nodeLogger = logging.getLogger("arduino")
logger = logging.getLogger("gateway")

class Main():
    def __init__(self, arduino_port, online, api_url, node_name, lm75):
        self.logger = logging.getLogger("gateway.main")
        self.online = online
        if online:
            self.api_urlv1 = api_url + "/api/v1"
            self.api_url_for_unlock = api_url + "/api/v2"
        self.node_name = node_name
        self.lm75 = lm75
        self.arduino = PyCmdMessenger.ArduinoBoard(arduino_port, baud_rate=9600)
        self.cmdMessenger = PyCmdMessenger.CmdMessenger(self.arduino, commands)

    def main(self):
        # init internal command server
        init_msg_server(self.cmdMessenger)

        # init REST connection
        if self.online:
            node_url = init_rest(self.api_urlv1, self.node_name)

            if node_url != None:
                self.logger.info("Node URL: %s", node_url)
                online = True
            else:
                self.logger.error("Failed to initialize REST")
                sys.exit(1)

        # turn on lm75 temperature logging when requested
        if self.lm75:
            self.cmdMessenger.send("request_lm75", True)

        # prepate event handler | simple REST
        event_handler = CmdEvents.CmdEvents(self.cmdMessenger)
        event_handler.addListener("send_log", on_send_log)
        if self.online:
            event_handler.addListener("send_temp",
                                      on_send_temp(self.api_urlv1, node_url))
            event_handler.addListener("send_pir",
                                      on_send_pir(self.api_urlv1, node_url))
            event_handler.addListener("request_uid_status",
                                      on_request_uid_status(self.api_url_for_unlock, node_url))

        if logger.isEnabledFor(logging.DEBUG):
            event_handler.addDebugListener(on_debug)

        # start event handler thread
        event_handler.start()

        #meh
        while True:
            time.sleep(10)

# debug print callbacks
def on_debug(msg):
    nodeLogger.debug(msg)

# REST callbacks
def on_send_log(msg):
    nodeLogger.debug(msg)

def on_send_temp(api_url, node_url):
    def call(msg):
        requests.post(api_url + "/temperatures",
                      json={"node": node_url, "value": msg})
    return call

def on_send_pir(api_url, node_url):
    def call(msg):
        requests.post(api_url + "/pirs",
                      json={"node": node_url})
    return call

def on_request_uid_status(api_url, node_url):
    def call(msg):
        r = requests.get(api_url + "/checkpermission/"
                     + string.split(node_url, "/")[-1] + "/" + msg)
        if r.status_code is 200:
            c.send("send_uid_status", True)
        else:
            c.send("send_uid_status", False)

# helpers
def init_rest(api_url, node_name):
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
        logger.debug("REST OK")
        json_data = json.loads(r.text)
        return json_data["_links"]["self"]["href"]

def init_msg_server(cmdMessenger):
    logging.debug('Serving on localhost:5050')
    server = MsgServer.MsgServer('localhost', 5050, cmdMessenger.send)
    loop_thread = threading.Thread(target=asyncore.loop, name="Asyncore Loop")
    loop_thread.daemon = True
    loop_thread.start()

if __name__ == "__main__":
    # simple command line parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", type=str, default="INFO", choices=["info", "debug"],
                        help="increase output verbosity")
    parser.add_argument("--online", type=str, metavar="PROTO://ADDRESS:PORT",
                        help="Enable online storage")
    parser.add_argument("--lm75", action="store_true", help="Use LM75 sensor")
    parser.add_argument("--name", default="default_node", metavar="NAME",
                        help="Name of the node")
    parser.add_argument("com", default="/dev/ttyACM0", metavar="COM_PORT",
                        help="COM port to use")
    args = parser.parse_args()

    conf_api_url = None
    conf_online = False
    if args.online != None:
        conf_api_url = args.online
        conf_online = True
    conf_node_name = args.name

    numeric_level = getattr(logging, args.verbosity.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(args.verbosity))
    logging.basicConfig(level=numeric_level)

    try:
        Main(args.com, conf_online, conf_api_url, conf_node_name, args.lm75).main()
    except KeyboardInterrupt:
        sys.exit()

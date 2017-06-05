from __future__ import print_function
import argparse
import asyncore
import json
import logging
import string
import sys
import threading
import time

import requests
import PyCmdMessenger
import MsgServer
import CmdEvents
#pylint: disable=missing-docstring
COMMANDS = [["send_log", "s"],
            ["send_temp", "d"],
            ["send_pir", ""],   # TODO: bug here, does not allow None
            ["request_lm75", "?"],
            ["send_mock", "s"],
            ["request_uid_status", "s"],
            ["send_uid_status", "?"],
            ["request_pir", "?"]]

nodeLogger = logging.getLogger("arduino")
logger = logging.getLogger("gateway")

class Main(object):
    def __init__(self, arduino_port, online, api_url, node_name, lm75):
        self.logger = logging.getLogger("gateway.main")
        self.online = online
        if online:
            self.api_urlv1 = api_url + "/api/v1"
            self.api_url_for_unlock = api_url + "/api/v2"
        self.node_name = node_name
        self.lm75 = lm75
        self.arduino = PyCmdMessenger.ArduinoBoard(arduino_port, baud_rate=9600)
        self.cmd_messenger = PyCmdMessenger.CmdMessenger(self.arduino, COMMANDS)

    def main(self):
        # init internal command server
        init_msg_server(self.cmd_messenger)

        # init REST connection
        if self.online:
            node_url = init_rest(self.api_urlv1, self.node_name)

            if node_url != None:
                self.logger.info("Node URL: %s", node_url)
            else:
                self.logger.error("Failed to initialize REST")
                sys.exit(1)

        # turn on lm75 temperature logging when requested
        if self.lm75:
            self.cmd_messenger.send("request_lm75", True)

        # prepate event handler | simple REST
        event_handler = CmdEvents.CmdEvents(self.cmd_messenger)
        event_handler.add_callback("send_log", on_send_log)
        if self.online:
            event_handler.add_callback("send_temp",
                                       on_send_temp(self.api_urlv1, node_url))
            event_handler.add_callback("send_pir",
                                       on_send_pir(self.api_urlv1, node_url))
            event_handler.add_callback("request_uid_status",
                                       on_request_uid_status(self.api_url_for_unlock, node_url, self.cmd_messenger))

        if logger.isEnabledFor(logging.DEBUG):
            event_handler.add_debug_callback(on_debug)

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
    def call(_):
        requests.post(api_url + "/pirs",
                      json={"node": node_url})
    return call

def on_request_uid_status(api_url, node_url, cmd_messenger):
    def call(msg):
        req = requests.get(api_url + "/checkpermission/"
                           + string.split(node_url, "/")[-1] + "/" + msg)
        if req.status_code == 200:
            cmd_messenger.send("send_uid_status", True)
        else:
            cmd_messenger.send("send_uid_status", False)
    return call

# helpers
def init_rest(api_url, node_name):
    req = requests.get(api_url)
    if req.status_code != 200:
        logger.error("check API URL")
        return None

    address = api_url + "/nodes/search/findByName?name=" + node_name
    req = requests.get(address)
    if req.status_code == 404:
        logger.warn("Node not found, creating!")
        req = requests.post(api_url + "/nodes", json={"name": "node_name"})
        if req.status_code == 201:
            json_data = json.loads(req.text)
            return json_data["_links"]["self"]["href"]
        else:
            logger.debug("%s %s", req.status_code, req.text)
            sys.exit("failed")
    else:
        logger.debug("REST OK")
        json_data = json.loads(req.text)
        return json_data["_links"]["self"]["href"]

def init_msg_server(cmd_messenger):
    logging.debug('Serving on localhost:5050')
    server = MsgServer.MsgServer('localhost', 5050, cmd_messenger.send) # pylint: disable=unused-variable
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

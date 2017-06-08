from __future__ import print_function
import argparse
import asyncore
import json
import logging
import string
import sys
import threading
import time
from urlparse import urlparse

import requests
import PyCmdMessenger
import paho.mqtt.client as mqtt

import MsgServer
import CmdEvents
import MyRest

#pylint: disable=missing-docstring
COMMANDS = [["send_log", "s"],
            ["send_temp", "d"],
            ["send_pir", ""],   # TODO: bug here, does not allow None
            ["request_lm75", "?"],
            ["send_mock", "s"],
            ["request_uid_status", "s"],
            ["send_uid_status", "?"],
            ["request_pir", "?"],
            ["force_unlock", ""]]

nodeLogger = logging.getLogger("arduino")
logger = logging.getLogger("gateway")

class MyApp(object):
    def __init__(self, arduino_port, api_url, mqtt_url, node_name, lm75):
        self.logger = logging.getLogger("gateway.main")
        if api_url != None:
            self.myrest = True
            self.api_urlv1 = api_url + "/api/v1"
            self.api_url_for_unlock = api_url + "/api/v2"
        self.mqtt_url = mqtt_url
        self.node_name = node_name
        self.lm75 = lm75
        self.arduino = PyCmdMessenger.ArduinoBoard(arduino_port, baud_rate=9600)
        self.cmd_messenger = PyCmdMessenger.CmdMessenger(self.arduino, COMMANDS)

    def main(self):
        # init internal command server
        init_msg_server(self.cmd_messenger)

        if self.mqtt_url != None:
            init_mqtt(self.cmd_messenger, self.mqtt_url, self.node_name)

        # turn on lm75 temperature logging when requested
        if self.lm75:
            self.cmd_messenger.send("request_lm75", True)

        # prepate event handler | simple REST
        event_handler = CmdEvents.CmdEvents(self.cmd_messenger)

        event_handler.add_callback("send_log", on_send_log)
        if logger.isEnabledFor(logging.DEBUG):
            event_handler.add_debug_callback(on_debug)

        # start event handler thread
        event_handler.start()

# debug print callbacks
def on_debug(msg):
    nodeLogger.debug(msg)

def on_send_log(msg):
    nodeLogger.info(msg)

def init_mqtt(cmd_messenger, mqtt_url, node_name):
    url = urlparse(mqtt_url)
    client = mqtt.Client()
    client.on_connect = on_connect(node_name)
    client.on_message = on_message(cmd_messenger)
    if url.scheme == "tcp":
        client.connect(url.hostname, url.port)
    else:
        raise Exception, "Unsupport URL scheme: " + mqtt_url
    client.loop_start()

def on_connect(name):
    def call(client, userdata, rc):
        logger.debug("MQTT client connected, subscribing ....")
        client.subscribe("/" + name +"/unlock")
    return call

def on_message(cmd_messenger):
    def call(client, userdata, msg):
        logger.info("Got force_unlock message for this node")
        cmd_messenger.send("force_unlock")
    return call

def init_msg_server(cmd_messenger):
    logging.debug('Serving on localhost:5050')
    server = MsgServer.MsgServer('localhost', 5050, cmd_messenger.send) # pylint: disable=unused-variable
    loop_thread = threading.Thread(target=asyncore.loop, name="Asyncore Loop")
    loop_thread.daemon = True
    loop_thread.start()

if __name__ == "__main__":

    def main():
        # simple command line parsing
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--verbosity", type=str, default="INFO", choices=["info", "debug"],
                            help="increase output verbosity")
        parser.add_argument("--myrest", type=str, metavar="PROTO://ADDRESS:PORT/DIR",
                            help="Enable online storage")
        parser.add_argument("--mymqtt", type=str, metavar="PROTO://ADDRESS:PORT/DIR",
                            help="Enable simple mqtt subcribe")
        parser.add_argument("--lm75", action="store_true", help="Use LM75 sensor")
        parser.add_argument("--name", default="default_node", metavar="NAME",
                            help="Name of the node")
        parser.add_argument("com", default="/dev/ttyACM0", metavar="COM_PORT",
                            help="COM port to use")
        args = parser.parse_args()

        conf_mqtt_url = None
        if args.mymqtt != None:
            conf_mqtt_url = args.mymqtt

        numeric_level = getattr(logging, args.verbosity.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: {}'.format(args.verbosity))
        logging.basicConfig(level=numeric_level)

        # init REST connection
        if args.myrest != None:
            myrest = MyRest.Myrest(args.myrest, args.name)
            node_url = myrest.init_rest()

            if node_url != None:
                self.logger.info("Node URL: %s", node_url)
            else:
                self.logger.error("Failed to initialize REST")
                sys.exit(1)

        app = MyApp(args.com, conf_api_url, conf_mqtt_url, conf_node_name, args.lm75).main()

    try:
        main()
        # meh
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        sys.exit()

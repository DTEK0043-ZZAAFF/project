#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""Helper to visualize MQTT messages
"""

from __future__ import print_function

__author__ = "Janne Kujanpää"
__version__ = "0.0.1"
__copyright__ = "Copyright (c) 2017 Janne Kujanpää"

__license__ = """
Copyright (c) 2017 Janne Kujanpää

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import argparse
import logging
import json
from urlparse import urlparse

import paho.mqtt.client as mqtt
from pyfiglet import Figlet

logger = logging.getLogger(__name__)

def main():
    """Execute helped script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", type=str, default="INFO",
                        choices=["info", "debug"], help="increase output verbosity")
    parser.add_argument("--sys", action="store_true", help="Enable $SYS")
    parser.add_argument("url", metavar="URL")

    args = parser.parse_args()
    # setup logger
    numeric_level = getattr(logging, args.verbosity.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(args.verbosity))
    logging.basicConfig(level=numeric_level)

    f = Figlet(font='slant', width=120)
    url = urlparse(args.url)
    if url.scheme == "tcp":
        transport = "tcp"
    elif url.scheme == "ws":
        transport = "websockets"

    client = mqtt.Client(transport=transport, userdata={"figlet": f, "sys":args.sys})
    client.on_connect = __on_connect
    client.on_message = __on_message
    if url.scheme == "tcp" or url.scheme == "ws":
        client.username_pw_set(url.username, url.password)
        client.connect(url.hostname, url.port, 60)
    else:
        raise Exception, "Unsupport URL scheme: " + args.url

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()

# The callback for when the client receives a CONNACK response from the server.
def __on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code "+str(rc))
    logger.debug("%s, %s", flags, rc)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/#")
    if userdata["sys"]:
        client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def __on_message(client, userdata, msg):
    # handle some well know with figlet
    if "/pir" in msg.topic:
        value = json.loads(msg.payload)["value"]
        if value:
            print(userdata["figlet"].renderText("Movement detected!"))
        else:
            print(userdata["figlet"].renderText("Movement end!"))
    elif "/unlock" in msg.topic:
        print(userdata["figlet"].renderText("Forced unlock!"))
    else:
        print(msg.topic + ": " + str(msg.payload))


if __name__ == "__main__":
    main()

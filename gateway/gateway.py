#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""IoT gateway for DTEL0043.

The main file: contain main function which binds all other classes to make
magic happen.

See other modules for more information about source code.
For other info consult READMEs, NOTES and project documentation.
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

# code in PyCmdMessenger has following license:
#
# Copyright (c) 2016 Mike Harms
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import logging
import sys
import time

import PyCmdMessenger

from myapp import CmdEvents
from myapp import MsgServer
from myapp import MyRest
from myapp import MyMqtt
from myapp import MyAws
from myapp import MyPyCmdMessengerMock

COMMANDS = [["send_log", "s"],
            ["send_temp", "d"],
            ["send_pir", "?"],
            ["request_lm75", "?"],
            ["send_mock", "s"],
            ["request_uid_status", "s"],
            ["send_uid_status", "?"],
            ["request_pir", "?"],
            ["force_unlock", ""]] # TODO: bug here, does not allow None
"""Methods for CmdMessenger

PyCmdMessenger uses this to check that incoming data values have correct types
and outgoing messages have valid tag and data type.

"""


def __on_debug(msg):
    """Log messages from arduino with debug priority/format.

    This function is used as callback function with PyCmdMessenger event handlers.

    Args:
        msg: message to log
    """
    logging.getLogger("arduino").debug(msg)

def __on_send_log(msg):
    """Log logging messages send from Arduino.

    This function is used as callback function with PyCmdMessenger event handlers.

    Args:
        msg: message to log
    """
    logging.getLogger("arduino").info(msg)

def __msgserver_callback(cmd_events):
    def __function(data):
        splitted_data = data.split(":", 2)
        if splitted_data[0].lower() == "arduino":
            cmd_events.cmd_messenger.send("send_mock", splitted_data[1])
        elif splitted_data[0].lower() == "local":
            if splitted_data[1] == "piru":
                cmd_events.inject_data("send_pir", [True])
            elif splitted_data[1] == "pird":
                cmd_events.inject_data("send_pir", [False])
            else:
                pass
        else:
            logging.getLogger(__name__).warn("Unknown command prefix")
    return __function

def main():
    """Run the app. Initializes all components and starts background threads."""
    logger = logging.getLogger("main")
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", type=str, default="INFO",
                        choices=["info", "debug"], help="increase output verbosity")
    parser.add_argument("--myrest", type=str, metavar="PROTO://ADDRESS:PORT/DIR",
                        help="Enable online storage")
    parser.add_argument("--mymqtt", type=str, metavar="PROTO://ADDRESS:PORT/DIR",
                        help="Enable simple mqtt subcribe")
    parser.add_argument("--aws", type=str, metavar="PATH/TO/CONFIG_DIR",
                        help="Enable AWS IoT")
    parser.add_argument("--lm75", action="store_true", help="Use LM75 sensor")
    parser.add_argument("--pir", action="store_true", help="Enable PIR sensor")
    parser.add_argument("--name", default="default_node", metavar="NAME",
                        help="Name of the node")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--noarduino", action="store_true", help="Disable Arduino node code")
    group.add_argument("--com", default="/dev/ttyACM0", metavar="COM_PORT",
                       help="COM port to use", required=False)
    args = parser.parse_args()

    # setup logger
    numeric_level = getattr(logging, args.verbosity.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(args.verbosity))
    logging.basicConfig(level=numeric_level)

    # Setup hardware. PyCmdMessenger is used as abstraction layer
    logger.info("Setting up hardware")
    if not args.noarduino:
        arduino = PyCmdMessenger.ArduinoBoard(args.com, baud_rate=9600)
        cmd_messenger = PyCmdMessenger.CmdMessenger(arduino, COMMANDS)
    else:
        # setup runtime mockup!
        cmd_messenger = MyPyCmdMessengerMock(COMMANDS) # pylint: disable=redefined-variable-type

    # Register basic event handlers: logging messges from arduino node
    # and if doing debug logging log all messages received from arduino
    logger.info("Initializing CmdMessenger event handler")
    event_handler = CmdEvents(cmd_messenger, args.noarduino)
    event_handler.add_callback("send_log", __on_send_log)
    if logger.isEnabledFor(logging.DEBUG):
        event_handler.add_debug_callback(__on_debug)

    # Setup extra server for incoming commands. Send received messages
    # to Arduino node which will parse messages. See node code for
    # supported messages
    logger.info("Initializing internal command handler")
    MsgServer.init_msg_server(__msgserver_callback(event_handler))

    # Initialize simple REST interface. Endpoint is out Java backend.
    # Note: if `MyRest.Myrest` exits process if connection fails
    logger.info("Initializing java based REST interface")
    if args.myrest != None:
        myrest = MyRest(args.myrest, args.name)
        myrest.register_callbacks(cmd_messenger, event_handler)

    # Initialize MQTT: Subscribe one MQTT message channel.
    logger.info("Initializing MQTT")
    if args.mymqtt != None:
        MyMqtt.init_mqtt(cmd_messenger, event_handler, args.mymqtt, args.name)

    # Load AWS IoT config and certs
    if args.aws:
        aws = MyAws(args.aws, event_handler, args.name)

    # Start event handler loop. Messages from Serial port are now
    # being polled
    logger.info("Starting CmdMessenger event handler message loop")
    event_handler.start()

    # Send commands to node to enable configured sensors
    logger.info("enabling sensors")
    if args.lm75:
        cmd_messenger.send("request_lm75", True)
    if args.pir:
        cmd_messenger.send("request_pir", True)

    logger.info("All done. Processing Arduino and MQTT messages")

if __name__ == "__main__":
    main()
    try:
        # main thread must be kep alive otherwise nothing captures CTRL+C
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, IOError):
        sys.exit()

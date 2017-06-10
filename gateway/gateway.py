#!/usr/bin/python2
""" IoT gateway for DTEL0043

The main file: contain main function which binds all other classes to make
magic happen.

See other modules for more information about source code.
For other info consult READMEs, NOTES and project documentation.
"""

from __future__ import print_function
import argparse
import logging
import sys
import time

import PyCmdMessenger

import MsgServer
import CmdEvents
import MyRest
import MyMqtt

COMMANDS = [["send_log", "s"],
            ["send_temp", "d"],
            ["send_pir", ""],   # FIX: bug here, does not allow None
            ["request_lm75", "?"],
            ["send_mock", "s"],
            ["request_uid_status", "s"],
            ["send_uid_status", "?"],
            ["request_pir", "?"],
            ["force_unlock", ""]]
""" Methods for CmdMessenger

PyCmdMessenger uses this to check that incoming data values have correct types
and outgoing messages have valid tag and data type.

"""


def __on_debug(msg):
    """ Callback function for CmdMessenger event handler.

    This function is registered to print all data received from Arduino

    Args:
        msg (list): message to log
    """
    logging.getLogger("arduino").debug(msg)

def __on_send_log(msg):
    """ Callback function for CmdMessenger event handler.

    Args:
        msg (str): message to log
    """
    logging.getLogger("arduino").info(msg)

def main():
    """ Main function. Initializes all components and starts background threads.
    """
    logger = logging.getLogger("main")
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", type=str, default="INFO",
                        choices=["info", "debug"], help="increase output verbosity")
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

    # setup logger
    numeric_level = getattr(logging, args.verbosity.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(args.verbosity))
    logging.basicConfig(level=numeric_level)

    # Setup hardware. PyCmdMessenger is used as abstraction layer
    logger.info("Setting up hardware")
    arduino = PyCmdMessenger.ArduinoBoard(args.com, baud_rate=9600)
    cmd_messenger = PyCmdMessenger.CmdMessenger(arduino, COMMANDS)

    # Setup extra server for incoming commands. Used to receive command
    # through TCP socket.
    logger.info("Initializing internal command handler")
    MsgServer.init_msg_server(cmd_messenger)

    # Register basic event handlers: logging messges from arduino node
    # and if doing debug logging log all messages received from arduino
    logger.info("Initializing CmdMessenger event handler")
    event_handler = CmdEvents.CmdEvents(cmd_messenger)
    event_handler.add_callback("send_log", __on_send_log)
    if logger.isEnabledFor(logging.DEBUG):
        event_handler.add_debug_callback(__on_debug)

    # Initialize simple REST interface. Endpoint is out Java backend.
    # Note: if `MyRest.Myrest` exits process if connection fails
    logger.info("Initializing java based REST interface")
    if args.myrest != None:
        myrest = MyRest.Myrest(args.myrest, args.name)
        myrest.register_callbacks(cmd_messenger, event_handler)

    # Initialize MQTT: Subscribe one MQTT message channel.
    logger.info("Initializing MQTT")
    if args.mymqtt != None:
        MyMqtt.init_mqtt(cmd_messenger, args.mymqtt, args.name)

    # Start event handler loop. Messages from Serial port are now
    # being polled
    logger.info("Starting CmdMessenger event handler message loop")
    event_handler.start()

    # Send commands to node to enable configured sensors
    logger.info("enabling sensors")
    if args.lm75:
        cmd_messenger.send("request_lm75", True)

    logger.info("All done. Processing Arduino and MQTT messages")

if __name__ == "__main__":
    main()
    try:
        # main thread must be kep alive otherwise nothing captures CTRL+C
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, IOError):
        sys.exit()

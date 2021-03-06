# -*- coding: utf-8 -*-
"""Event handler for PyCmdMessenger."""

__author__ = "Janne Kujanpää"
__copyright__ = "Copyright (c) 2017 Janne Kujanpää"
__license__ = "MIT"

import logging
import collections
import sys
import threading
import thread

from serial import SerialException

class CmdEvents(threading.Thread):
    """Event hander class for PyCmdMessenger.

    Simple event handled for PyCmdMessenger.

    Create instance, add callbacks if needed and start background thread with
    `start()`.

    TODO: document callbacks
    """

    def __init__(self, cmd_messenger, disable_poll=False):
        """Create new instance.

        Args:
            cmd_messenger: PyCmdMessenger instance to poll and send messages into
        """
        threading.Thread.__init__(self)
        self.daemon = True
        self.logger = logging.getLogger("CmdEvents")
        self.cmd_messenger = cmd_messenger
        self.disable_poll = disable_poll
        self.callbacks = collections.defaultdict(list)
        self.debug_callbacks = []
        self.default_callback = self.__default_callback
        self.default_receive_error_callback = self.__default_receive_error_callback

    def add_callback(self, message_type, func):
        """Add callback function for defined type.

        Function will receive one argument. Argument type is None, single message or list

        Args:
            message_type: type of the message for `func`
            func: function to add
        """
        if self.__message_type_valid(message_type):
            self.callbacks[message_type].append(func)
        else:
            raise Exception, "Messagetype not found: " + message_type

    def add_debug_callback(self, func):
        """Add debug callback.

        Adds debug callback function. Function will be called with full received message

        Args:
            func: function to add
        """
        self.debug_callbacks.append(func)

    def __message_type_valid(self, message_type):
        """Check if `message_type` is found on PyCmdMessenger command list.

        Args:
            message_type: type to check
        """
        for command in self.cmd_messenger.commands:
            if command[0] == message_type:
                return True
        return False

    def run(self):
        """Implement inherited method."""
        if not self.disable_poll:
            while True:
                self.__read_once()

    def __read_once(self):
        """Execute `CmdMessenger.receive()` once."""
        # read message Arduino node. PyCmdMessenger gives up after 1 second timeout
        # and return None
        try:
            message = self.cmd_messenger.receive()
        except ValueError:
            # edge case. in some cased when starting Arduino it sends
            # few bytes of random(?) data. Ignore error
            # TODO: proper fix?
            self.logger.warn("Reading message failed: ", exc_info=True)
            message = None
        except SerialException:
            # Run callback when device is disconnected
            self.default_receive_error_callback()
        except Exception: #pylint: disable=broad-except
            # Run callback when unknown error happened while Reading
            # data from device
            self.default_receive_error_callback()

        if message is None:
            pass
        else:
            self.__handle_message(message)

    def inject_data(self, label, message):
        """Inject data.

        Emulates received data
        """
        self.__handle_message([label, message, None])

    def __handle_message(self, message):
        # first pass message to debug
        for callback in self.debug_callbacks:
            try:
                callback(message)
            except SerialException: #pylint: disable=broad-except
                self.logger.warn("debug callback function failed: ", exc_info=True)

        # find the callbacks
        callback_fns = self.callbacks.get(message[0])
        # if call back for type is not found process message with default
        # callbacks
        if callback_fns is None:
            try:
                self.default_callback(message[0], message[1])
            except Exception: #pylint: disable=broad-except
                self.logger.warn("default callback function failed: ", exc_info=True)
            return

        # Mangle message for callback method
        # Implementor of callback method knows message type
        if not message[1]:
            msg = None
        elif len(message[1]) == 1:
            msg = message[1][0]
        else:
            msg = message[1]
        # finally pass message to callback functions
        for callback_fn in callback_fns:
            try:
                callback_fn(msg)
            except Exception: #pylint: disable=broad-except
                self.logger.warn("callback function failed: ", exc_info=True)

    def __default_callback(self, mtype, msg):
        self.logger.warn("Unregistered message_type: %s msg: %s", mtype, msg)

    def __default_receive_error_callback(self):
        self.logger.warn("Reading message failed: ", exc_info=True)
        thread.interrupt_main()
        sys.exit()

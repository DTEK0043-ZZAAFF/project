import logging
import collections
import threading

class CmdEvents(threading.Thread):
    def __init__(self, cmd_messenger):
        threading.Thread.__init__(self)
        self.daemon = True
        self.logger = logging.getLogger("CmdEvents")
        self.cmd_messenger = cmd_messenger
        self.listeners = collections.defaultdict(list)
        self.debug_listeners = []
        self.default_listener_fn = self.default_listener

    def set_default_callback(self, listener):
        self.default_listener_fn = listener

    def add_callback(self, message_type, func):
        if self.message_type_valid(message_type):
            self.listeners[message_type].append(func)
        else:
            raise Exception, "Messagetype not found: " + message_type

    def add_debug_callback(self, func):
        self.debug_listeners.append(func)

    def message_type_valid(self, message_type):
        for command in self.cmd_messenger.commands:
            if command[0] == message_type:
                return True
        return False

    def run(self):
        while True:
            self.read_once()

    def read_once(self):
        try:
            message = self.cmd_messenger.receive()
        except (IOError, ValueError):
            message = None
            self.logger.warn("Reading message failed: ", exc_info=True)

        if message is None:
            pass
        else:
            # first pass message to debug
            for listener in self.debug_listeners:
                listener(message)

            # find the listeners
            listener_fns = self.listeners.get(message[0])
            # if none found => default
            if listener_fns is None:
                self.default_listener_fn(message[0], message[1])
                return

            # pass one argument to handler
            # implementor knows what type argument will be
            if not message[1]:
                msg = None
            elif len(message[1]) == 1:
                msg = message[1][0]
            else:
                msg = message[1]
            # finally pass message to callback functions
            for listener_fn in listener_fns:
                listener_fn(msg)

    def default_listener(self, mtype, msg):
        self.logger.warn("Unknown message_type: %s", mtype)
        self.logger.warn("with message: %s", msg)

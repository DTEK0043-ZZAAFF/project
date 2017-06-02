import logging
import traceback

class CmdEvents():
    def __init__(self, cmdMessenger):
        self.cmdMessenger = cmdMessenger
        self.listeners = {}
        self.default_listener_fn = self.default_listener

    def setDefaultListener(self, listener):
        self.default_listener_fn = listener

    def addListener(self, str, fn):
        if self.cmdMessenger.commands:
            self.listeners[str] = fn
        else:
            raise Exception, "Command not found: " + str

    def isMessageTypeValid(self, str):
        for x in self.cmdMessenger.commands:
            if x[0] == str:
                return True
        return False

    def run(self):
        while True:
            readOnce(self)

    def readOnce(self):
        try:
            message = self.cmdMessenger.receive()
        except Exception as e:
            message = None
            logging.warn(traceback.format_exc())

        if message == None:
            pass
        else:
            listener_fn = self.listeners.get(message[0])
            if listener_fn == None:
                self.default_listener_fn(message[0], message[1])
                return

            # pass one argument to handler
            # implementor knows what type argument will be
            if len(message[1]) == 0:
                msg = None
            elif len(message[1]) == 1:
                msg = message[1][0]
            else:
                msg = message[1]
            listener_fn(msg)

    def default_listener(self, mtype, msg):
        logging.warn("Unknown message_type: %s", mtype)
        logging.warn("with message: %s", msg)

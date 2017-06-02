import logging
import traceback

class CmdEvents():
    def __init__(self, cmdMessenger):
        self.cmdMessenger = cmdMessenger
        self.logger = logging.getLogger("CmdEvents")
        self.listeners = {}

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
            try:
                message = self.cmdMessenger.receive()
            except Exception as e:
                message = None
                self.logger.warn(traceback.format_exc())

            if message == None:
                pass
            else:
                listener_fn = self.listeners.get(message[0], self.default_listener)
                # pass one argument to handler
                # implementor knows what type argument will be
                if len(message) == 0:
                    msg = None
                elif len(message) == 1:
                    msg = message[1][0]
                else:
                    msg = message
                listener_fn(msg)

    def default_listener(self):
        self.logger.warn("Unknown message_type: %s", message_type)
        self.logger.warn("with message: %s", message[1])

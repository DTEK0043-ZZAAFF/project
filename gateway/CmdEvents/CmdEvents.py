import logging
import collections
import threading

class CmdEvents(threading.Thread):
    def __init__(self, cmdMessenger):
        threading.Thread.__init__(self)
        self.daemon = True
        self.logger = logging.getLogger("CmdEvents")
        self.cmdMessenger = cmdMessenger
        self.listeners = collections.defaultdict(list)
        self.debugListeners = []
        self.default_listener_fn = self.default_listener

    def setDefaultListener(self, listener):
        self.default_listener_fn = listener

    def addListener(self, str, fn):
        if self.isMessageTypeValid(str):
            self.listeners[str].append(fn)
        else:
            raise Exception, "Messagetype not found: " + str

    def addDebugListener(self, fn):
        self.debugListeners.append(fn)

    def isMessageTypeValid(self, str):
        for x in self.cmdMessenger.commands:
            if x[0] == str:
                return True
        return False

    def run(self):
        while True:
            self.readOnce()

    def readOnce(self):
        try:
            message = self.cmdMessenger.receive()
        except Exception as e:
            message = None
            self.logger.warn("Reading message failed: ", {"exc_info": True})

        if message == None:
            pass
        else:
            # first pass message to debug
            for listener in self.debugListeners:
                listener(message)

            # find the listeners
            listener_fns = self.listeners.get(message[0])
            # if none found => default
            if listener_fns == None:
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
            # finally pass message to callback functions
            for listener_fn in listener_fns:
                listener_fn(msg)

    def default_listener(self, mtype, msg):
        self.logger.warn("Unknown message_type: %s", mtype)
        self.logger.warn("with message: %s", msg)

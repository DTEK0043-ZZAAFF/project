"""Message server for runtime mock messages."""

__author__ = "Janne Kujanpää"
__copyright__ = "Copyright (c) 2017 Janne Kujanpää"
__license__ = "MIT"

import asyncore
import logging
import socket
import threading

class _MsgServer(asyncore.dispatcher):
    """Internal TCP server. Receives simple messages over TCP socket.

    Sends messages with given function. Caller selects function to use.
    """

    def __init__(self, host, port, func):
        """Create new instance.

        Args:
            host: host to bind
            port: port to bind
            func: Function used to send mock messages
        """
        asyncore.dispatcher.__init__(self)
        self.logger = logging.getLogger("MsgServer")
        self.func = func
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((host, port))
        self.logger.debug("Binding to %s", self.socket.getsockname)
        self.listen(1)

    def handle_accept(self):
        """Implement inherited class."""
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            self.logger.debug("Incoming connection from %s", repr(addr))
            _ = _MsgHandler(sock, self.func)

class _MsgHandler(asyncore.dispatcher):
    """Message handler for MsgServer."""

    def __init__(self, sock, func, chunk_size=256):
        """Create new instance.

        Args:
            sock: new socket to read from
            func: Function used to send mock messages
        """
        asyncore.dispatcher.__init__(self, sock=sock)
        self.logger = logging.getLogger("MsgHandler")
        self.chunk_size = chunk_size
        self.data_to_write = []
        self.func = func

    def handle_read(self):
        """Implement inherited class."""
        data = self.recv(self.chunk_size)
        # TODO: add a way to contol gateway.py
        # e.g. enable sensors without command line args
        self.logger.debug("Read: %s", data)
        self.func(data)
        self.send("OK")
        self.close()

def init_msg_server(func):
    """Initialize MsgServer and start background threads.

    Args:
        func: Function used to send mock messages
    """
    _ = _MsgServer('localhost', 50505, func) # pylint: disable=unused-variable
    loop_thread = threading.Thread(target=asyncore.loop, name="Asyncore Loop")
    loop_thread.daemon = True
    loop_thread.start()

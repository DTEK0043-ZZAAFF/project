import asyncore
import logging
import socket

class MsgServer(asyncore.dispatcher):
    def __init__(self, host, port, func):
        asyncore.dispatcher.__init__(self)
        self.logger = logging.getLogger("MsgServer")
        self.func = func
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((host, port))
        self.logger.debug("Binding to %s", self.socket.getsockname)
        self.listen(1)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            self.logger.debug("Incoming connection from %s", repr(addr))
            _ = MsgHandler(sock, self.func)

class MsgHandler(asyncore.dispatcher):
    def __init__(self, sock, func, chunk_size=256):
        asyncore.dispatcher.__init__(self, sock=sock)
        self.logger = logging.getLogger("MsgHandler")
        self.chunk_size = chunk_size
        self.data_to_write = []
        self.func = func

    def handle_read(self):
        data = self.recv(self.chunk_size)
        # TODO: add a way to contol gateway.py
        # e.g. enable sensors without command line args
        self.logger.debug("Read: %s", data)
        self.func("send_mock", data)
        self.send("OK")
        self.close()

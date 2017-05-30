import asyncore
import logging
import socket
import string

class MsgServer(asyncore.dispatcher):
    def __init__(self, host, port, fn):
        asyncore.dispatcher.__init__(self)
        self.logger = logging.getLogger("MsgServer")
        self.fn = fn
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((host, port))
        self.logger.debug("Binding to %s", self.socket.getsockname)
        self.listen(1)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            self.logger.debug("Incoming connection from %s", repr(addr))
            handler = MsgHandler(sock, self.fn)

class MsgHandler(asyncore.dispatcher):
    def __init__(self, sock, fn, chunk_size=256):
        asyncore.dispatcher.__init__(self, sock=sock)
        self.logger = logging.getLogger("MsgHandler")
        self.chunk_size = chunk_size
        self.data_to_write = []
        self.fn = fn

    def handle_read(self):
        data = self.recv(self.chunk_size)
        self.logger.debug("Read: %s", data)
        (command, message) = string.split(data, ":", 1)
        self.fn("send_mock", message)
        self.send("OK")
        self.close()

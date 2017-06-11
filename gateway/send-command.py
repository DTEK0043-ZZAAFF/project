from __future__ import print_function
import asyncore
import logging
import socket
import sys

__author__ = "Janne Kujanpää"
__copyright__ = "Copyright (c) 2017 Janne Kujanpää"
__license__ = "CC0 1.0 Universal, https://creativecommons.org/publicdomain/zero/1.0/legalcode"

def main():
    if len(sys.argv) != 4:
        print("Usage: mock.py <host> <port> <message>")
    MockClient(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    asyncore.loop(1)

class MockClient(asyncore.dispatcher):
    def __init__(self, host, port, message):
        asyncore.dispatcher.__init__(self)
        self.logger = logging.getLogger('MockClient')
        logging.basicConfig(level=logging.DEBUG)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.buffer = message

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_read(self):
        data = self.recv(8192)
        if data == 'OK':
            self.logger.debug("Got \"OK\". Exiting now...")
            self.close()

    def writable(self):
        return len(self.buffer) > 0

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]


if __name__ == "__main__":
    main()

from __future__ import print_function
import sys
import json
import logging
import threading
import asyncore
import socket
import string
import requests

import PyCmdMessenger

arduino_port = sys.argv[1]
api_url = sys.argv[2]
node_name = sys.argv[3]

# Usage: c:\Python27\python.exe foo.py COM5 http://localhost:8080/api/v1a bar aa
# python.exe foo.py <com port> <api address> <node name> <arg to enable lm75>
def main():
    global c
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("main")
    online = False
    lm75 = False
    if len(sys.argv) > 4:
        lm75 = True

    # init internal command server
    init_msg_server()

    # init REST connection
    node_url = init_rest()

    if node_url != None:
        logger.info("Node URL: %s", node_url)
        online = True

    # init arduino and CmdMessenger
    arduino = PyCmdMessenger.ArduinoBoard(arduino_port, baud_rate=9600)

    commands = [["send_log", "s"],
                ["send_temp", "d"],
                ["send_pir", ""],
                ["request_lm75", ""],
                ["send_mock", "s"]]

    c = PyCmdMessenger.CmdMessenger(arduino, commands)

    # turn on lm75 temperature logging when requested
    if lm75:
        c.send("request_lm75")

    while True:
        message = c.receive()
        if message == None:
            logger.debug("No message!")
        else:
            message_type = message[0]
            msg = message[1][0]
            if message_type is "send_log":
                logger.debug(msg)
            elif message_type is "send_temp":
                logger.debug("temp: %s", msg)
                online and requests.post(api_url + "/temperatures",
                                         json={"node": node_url, "value": msg})
            elif message_type is "send_pir":
                logger.debug("PIR detection!")
                online and requests.post(api_url + "/pirs",
                                         json={"node": node_url})
            else:
                logger.warn("Unknown message_type: %s", message_type)
                logger.warn("with message: %s", message[1])

def init_rest():
    r = requests.get(api_url)
    if r.status_code != 200:
        logger.error("check API URL")
        return None

    address = api_url + "/nodes/search/findByName?name=" + node_name
    r = requests.get(address)
    if r.status_code == 404:
        logger.warn("Node not found, creating!")
        r = requests.post(api_url + "/nodes", json={"name": "node_name"})
        if r.status_code == 201:
            json_data = json.loads(r.text)
            return json_data["_links"]["self"]["href"]
        else:
            logger.debug("%s %s", r.status_code, r.text)
            sys.exit("failed")
    else:
        json_data = json.loads(r.text)
        return json_data["_links"]["self"]["href"]

def init_msg_server():
    logging.debug('Serving on localhost:5050')
    server = MsgServer('localhost', 5050)
    loop_thread = threading.Thread(target=asyncore.loop, name="Asyncore Loop")
    loop_thread.daemon = True
    loop_thread.start()

class MsgServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.logger = logging.getLogger("MsgServer")
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((host, port))
        self.logger.debug("Binding to %s", self.socket.getsockname )
        self.listen(1)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            self.logger.debug("Incoming connection from %s", repr(addr))
            handler = MsgHandler(sock)

class MsgHandler(asyncore.dispatcher):
    def __init__(self, sock, chunk_size=256):
        asyncore.dispatcher.__init__(self, sock=sock)
        self.logger = logging.getLogger("MsgHandler")
        self.chunk_size = chunk_size
        self.data_to_write = []

    def handle_read(self):
        data = self.recv(self.chunk_size)
        self.logger.debug("Read: %s", repr(data))
        (command, message) = string.split(data, ":", 1)
        c.send("send_mock", message)
        self.send("OK")
        self.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()

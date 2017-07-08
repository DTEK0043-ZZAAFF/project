"""Helper module for AWS IoT"""
import ConfigParser
import glob
import json
import logging
import os

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

class MyAws(object):
    """AWS IoT support class.

    Configuration directory is passed as command line argument.
    See examples/config.ini for reference

    config.ini and certificate files are all in previously mentioned directory
    only one set of certificates is supported
    """

    def __init__(self, config_dir, cmd_messenger_event_handler, clientid):
        self.logger = logging.getLogger(__name__)
        self.event_handler = cmd_messenger_event_handler
        self.clientid = clientid

        self.__load_config(config_dir)
        self.__register_callbacks()

    def __load_config(self, config_dir):
        expanded_dir = os.path.expanduser(config_dir)
        if os.path.isdir(config_dir):
            # set endpoint
            config = ConfigParser.ConfigParser()
            config.read(os.path.join(expanded_dir, "config.ini"))
            aws_endpoint = config.get("default", "endpoint")
            # set keys
            certificate = self.__glob_one_file(
                os.path.join(expanded_dir, "*-certificate.pem.crt"))
            private = self.__glob_one_file(os.path.join(expanded_dir, "*-private.pem.key"))
            root_ca = self.__glob_one_file(os.path.join(expanded_dir, "Veri*.pem"))
            # setup MQTT
            self.client = AWSIoTMQTTClient(self.clientid)
            self.client.configureEndpoint(aws_endpoint, 8883)
            self.client.configureCredentials(root_ca, private, certificate)
        else:
            raise Exception("Given path not a directory: ")

    @staticmethod
    def __glob_one_file(path):
        files = glob.glob(path)
        if len(files) == 1:
            return files[0]
        elif not files:
            raise Exception("File not found: ")
        else:
            raise Exception("Found multiple files: ")

    def __register_callbacks(self):
        """Register CmdMessenger event handler and AWS IoT MQTT callbacks"""
        # register local PyCmdMessenger callbacks
        self.event_handler.add_callback("send_temp", self.__on_send_temp)
        self.event_handler.add_callback("send_pir", self.__on_send_pir)
        # register MQTT callbacks
        self.client.connect()
        self.client.subscribe("/pir", 1, self.__on_mqtt_all)

    def __on_send_temp(self, msg):
        message = json.dumps({"payload": {"temp": msg}})
        self.client.publish(self.clientid + "/temp", message, 1)

    def __on_send_pir(self, msg):
        message = json.dumps({"payload": {"value": msg}})
        self.client.publish(self.clientid + "/temp", message, 1)

    def __on_mqtt_all(self, client, userdata, message):
        self.logger.info("Received a new message: ")
        self.logger.info(message.payload)
        self.logger.info("from topic: ")
        self.logger.info(message.topic)
        self.logger.info("--------------\n\n")

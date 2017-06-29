"""Helper module for AWS IoT"""
import logging
import os

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

class MyAws(object):
    """AWS IoT support class.

    Configuration is read from file TODO

    Certificates in TODO
    """

    def __init__(self, config_dir, cmd_messenger):
        self.logger = logging.getLogger(__name__)
        self.cmd_messenger = cmd_messenger

        self.__load_config(config_dir)
        self.__register_callbacks()

    def __load_config(self, config_dir):
        if os.path.isdir(config_dir):
            pass
            # check keys
            # set keys
            # load config
            # sanity check for endpoint
        else:
            raise Exception("Not a directory: ")

    def start(self):
        """Start message loop"""
        pass

    def stop(self):
        """Stop MQTT message processing thread"""
        pass

    def __initialize(self):
        """Initialize MQTT connection"""
        pass

    def __register_callbacks(self):
        """Register CmdMessenger event handler and AWS IoT MQTT callbacks"""
        self.cmd_messenger.add_callback("send_temp", self.__on_send_temp)
        self.cmd_messenger.add_callback("send_pir", self.__on_send_pir)
        # TODO: MQTT

    def __on_send_temp(self, msg):
        pass

    def __on_send_pir(self, msg):
        pass

""" Encapsulates MQTT initialization and callbacks """

__author__ = "Janne Kujanpää"
__copyright__ = "Copyright (c) 2017 Janne Kujanpää"
__license__ = "MIT"

import logging
from urlparse import urlparse

import paho.mqtt.client as mqtt

def init_mqtt(cmd_messenger, mqtt_url, node_name):
    """
    Initializes MQTT.

    Initializes Paho MQTT library with given endpoint and subcribes one
    message topic(/`node_name`/unlock)

    Args:
        cmd_messenger: PyCmdMessenger instance to communicate with
        mqtt_url: URL to connect
        node_name: name of the node
    """
    url = urlparse(mqtt_url)
    client = mqtt.Client()
    client.on_connect = __on_connect(node_name)
    client.on_message = __on_message(cmd_messenger)
    # supports only plain TCP connections. Should support TLS websockets over
    # https!
    if url.scheme == "tcp":
        client.connect(url.hostname, url.port)
    else:
        raise Exception, "Unsupport URL scheme: " + mqtt_url
    client.loop_start()

def __on_connect(name):
    """ Creates callback function which is called on successful MQTT connect """
    def call(client, userdata, rc): # pylint: disable=invalid-name,unused-argument
        logging.debug("MQTT client connected, subscribing ....")
        client.subscribe("/" + name +"/unlock")
    return call

def __on_message(cmd_messenger):
    """ Creates callback function which is called on receiving MQTT message """
    def call(client, userdata, msg): # pylint: disable=invalid-name,unused-argument
        # NOTE: if we subscribe more topics we must check topis before
        # forwarding call to `PyCmdMessenger` instance
        logging.info("Got force_unlock message for this node")
        cmd_messenger.send("force_unlock")
    return call

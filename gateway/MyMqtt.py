import logging
from urlparse import urlparse

import paho.mqtt.client as mqtt

def init_mqtt(cmd_messenger, mqtt_url, node_name):
    url = urlparse(mqtt_url)
    client = mqtt.Client()
    client.on_connect = on_connect(node_name)
    client.on_message = on_message(cmd_messenger)
    if url.scheme == "tcp":
        client.connect(url.hostname, url.port)
    else:
        raise Exception, "Unsupport URL scheme: " + mqtt_url
    client.loop_start()

def on_connect(name):
    def call(client, userdata, rc): # pylint: disable=invalid-name,unused-argument
        logging.debug("MQTT client connected, subscribing ....")
        client.subscribe("/" + name +"/unlock")
    return call

def on_message(cmd_messenger):
    def call(client, userdata, msg): # pylint: disable=invalid-name,unused-argument
        logging.info("Got force_unlock message for this node")
        cmd_messenger.send("force_unlock")
    return call

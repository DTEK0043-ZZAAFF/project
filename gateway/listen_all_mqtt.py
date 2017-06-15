import sys
from urlparse import urlparse

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


# Start
url = urlparse(sys.argv[1])
if url.scheme == "tcp":
    transport = "tcp"
elif url.scheme == "ws":
    transport = "websockets"

client = mqtt.Client(transport=transport)
client.on_connect = on_connect
client.on_message = on_message
if url.scheme == "tcp" or url.scheme == "ws":
    client.username_pw_set(url.username, url.password)
    client.connect(url.hostname, url.port, 60)
else:
    raise Exception, "Unsupport URL scheme: " + mqtt_url

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()

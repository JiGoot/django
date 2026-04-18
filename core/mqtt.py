# trips/mqtt_client.py
import json
import paho.mqtt.client as mqtt

MQTT_HOST = "64ba2160b0dd4f438c323e27333c2ba1.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "hivemq.webclient.1767456970866"
MQTT_PASSWORD = "T#*z@s9Y48!qRX6tyZJv"


"""
_client.loop_start() explained

It starts a background thread that runs the network loop automatically.
Responsibilities of this loop:
Send outgoing messages (publishes)
Receive incoming messages (subscribes)
Send keep-alive pings to the broker
Handle reconnects if the connection drops

Without it:
client.publish() might fail or block
Subscriptions won’t receive messages
Keep-alive pings won’t be sent → broker may disconnect
"""

_client = None


def get_client():
    global _client
    if _client is None:
        _client = mqtt.Client()
        _client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        _client.tls_set()
        _client.connect(MQTT_HOST, MQTT_PORT, 60)
        _client.loop_start()  # keep network loop running, background thread
    return _client


"""Broker stores last retained message per topic
Any new subscriber immediately receives it
Useful for “latest driver location” or “status”"""


def publish_message(topic, payload, qos=1, retain=False):
    client = get_client()
    client.publish(topic, json.dumps(payload), qos=qos, retain=retain)

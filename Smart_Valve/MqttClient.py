import paho.mqtt.client as mqttClient
import time
import json
import ssl
import os
from SmartValve.settings import BASE_DIR

'''
global variables
'''
ROOT_FOLDER="certificates"
connected = False  # Stores the connection status
BROKER_ENDPOINT = "ec2-18-223-193-51.us-east-2.compute.amazonaws.com"
TLS_PORT = 8883
MQTT_USERNAME = "opp"
MQTT_PASSWORD = ""
TOPIC = "$awalk/A9_module/867959032005743/get"
DEVICE_LABEL = "a9_ssl"
TLS_CERT_PATH = os.path.join(BASE_DIR,ROOT_FOLDER,"ca.crt")
CLIENT_CERT = os.path.join(BASE_DIR, ROOT_FOLDER, "ip-172-31-28-113.us-east-2.compute.internal.crt")
CLIENT_KEY = os.path.join(BASE_DIR, ROOT_FOLDER, "ip-172-31-28-113.us-east-2.compute.internal.key")

'''
Functions to process incoming and outgoing streaming
'''


class MqttClient:

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:

            print("[INFO] Connected to broker")
            global connected  # Use global variable
            connected = True  # Signal connection
        else:
            print("[INFO] Error, connection failed")


    def on_publish(self, client, userdata, result):
        print("Published!")


    def connect(self, mqtt_client, mqtt_username, mqtt_password, broker_endpoint, port):
        global connected

        if not connected:
            mqtt_client.username_pw_set(mqtt_username, password=mqtt_password)
            mqtt_client.on_connect = self.on_connect
            mqtt_client.on_publish = self.on_publish
            mqtt_client.tls_set(ca_certs=TLS_CERT_PATH, certfile=CLIENT_CERT,
                                keyfile=CLIENT_KEY, cert_reqs=ssl.CERT_REQUIRED,
                                tls_version=5, ciphers=None)
            mqtt_client.tls_insecure_set(False)
            mqtt_client.connect(broker_endpoint, port=port)
            mqtt_client.loop_start()

            attempts = 0

            while not connected and attempts < 5:  # Wait for connection
                print(connected)
                print("Attempting to connect...")
                time.sleep(1)
                attempts += 1

        if not connected:
            print("[ERROR] Could not connect to broker")
            return False

        return True


    def publish(self, mqtt_client, topic, payload):
        try:
            mqtt_client.publish(topic, payload)

        except Exception as e:
            print("[ERROR] Could not publish data, error: {}".format(e))

    def main(self, payload, topic):
        mqtt_client = mqttClient.Client()
        ssl.match_hostname = lambda cert, hostname: True

        if not self.connect(mqtt_client, MQTT_USERNAME,
                       MQTT_PASSWORD, BROKER_ENDPOINT, TLS_PORT):
            return False

        self.publish(mqtt_client, topic , payload)

        return True

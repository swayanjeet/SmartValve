
import paho.mqtt.client as mqttClient
import time
import json
import ssl

'''
global variables
'''

connected = False  # Stores the connection status
BROKER_ENDPOINT = "ec2-18-223-193-51.us-east-2.compute.amazonaws.com"
TLS_PORT = 8883  
MQTT_USERNAME = "opp" 
MQTT_PASSWORD = ""  
TOPIC = "$awalk/A9_module/867959032005743/get"
DEVICE_LABEL = "a9_ssl"
TLS_CERT_PATH = "/home/awalk/ca.crt" 
CLIENT_CERT = "/home/awalk/ip-172-31-28-113.us-east-2.compute.internal.crt"
CLIENT_KEY ="/home/awalk/ip-172-31-28-113.us-east-2.compute.internal.key"

'''
Functions to process incoming and outgoing streaming
'''

def on_connect(client, userdata, flags, rc):
    if rc == 0:

        print("[INFO] Connected to broker")
        global connected  # Use global variable
        connected = True  # Signal connection
    else:
        print("[INFO] Error, connection failed")


def on_publish(client, userdata, result):
    print("Published!")


def connect(mqtt_client, mqtt_username, mqtt_password, broker_endpoint, port):
    global connected

    if not connected:
        mqtt_client.username_pw_set(mqtt_username, password=mqtt_password)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_publish = on_publish
        mqtt_client.tls_set(ca_certs=TLS_CERT_PATH, certfile=CLIENT_CERT,
                            keyfile=CLIENT_KEY, cert_reqs=ssl.CERT_REQUIRED,
                            tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
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


def publish(mqtt_client, topic, payload):

    try:
        mqtt_client.publish(topic, payload)

    except Exception as e:
        print("[ERROR] Could not publish data, error: {}".format(e))


def main():
    payload = json.dumps({"tls_publish_test": 20})

    #topic = "{}{}".format(TOPIC, DEVICE_LABEL)

    #print topic

    mqtt_client = mqttClient.Client()
    ssl.match_hostname = lambda cert, hostname: True

    if not connect(mqtt_client, MQTT_USERNAME,
                   MQTT_PASSWORD, BROKER_ENDPOINT, TLS_PORT):
        return False

    publish(mqtt_client, TOPIC , payload)

    return True


if __name__ == '__main__':
    while True:
        main()
        time.sleep(10)

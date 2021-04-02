import paho.mqtt.client as mqtt
import json5

class MqttSender(object):
    def __init__(self, config):
        self.host = config['host']
        self.token = config['token']
        self.port = config['port']
        self.client =  mqtt.Client()

    def start(self):
        self.client.username_pw_set(self.token)
        self.client.connect(self.host, self.port)
        self.client.loop_start()
        print('Sender start!')

    def send(self, message):
        if not self.client.is_connected:
            print('Sender haven\'t connected yet')
            return
        self.client.publish('v1/devices/me/telemetry', json5.dumps(message), 1)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        print('Sender stop!')

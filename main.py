import json5
from Checker import Checker
from MqttSender import MqttSender
import time

if __name__=="__main__":
    print('start!')
    file = open('./config.json', 'r')
    config = json5.load(file)
    file.close()
    checker = Checker(config['router'])
    mqttSender = MqttSender(config['thingsboard'])
    try:
        mqttSender.start()
        checker.login()
        while (1 != 0):
            read_time = time.time()
            response = checker.get_system_state()
            tx = response['result'][1][0]['tx_bps']
            rx = response['result'][1][0]['rx_bps']
            cpu = response['result'][2]['cpu']
            mem = response['result'][2]['mem']
            print('tx: {} KB/s, rx: {} KB/s, cpu: {}%, mem: {}%'.format(tx, rx, cpu, mem))

            message = {
                "tx": tx,
                "rx": rx,
                "cpu": cpu,
                "men": mem
            }
            mqttSender.send(message)
            sleep = config['interval'] - (time.time() - read_time)
            time.sleep(sleep if sleep > 0 else 0)
    except KeyboardInterrupt as e:
        checker.logout()
        mqttSender.stop()
        print('End!')
        exit(1)
        

    
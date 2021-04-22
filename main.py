import json5
from Checker import Checker
from MqttSender import MqttSender
import time

def work(checker, mqttSender):
    while (1 != 0):
        read_time = time.time()
        response = checker.get_system_state()
        tx = response['result'][1][0]['tx_bps']
        rx = response['result'][1][0]['rx_bps']
        cpu = response['result'][2]['cpu']
        mem = response['result'][2]['mem']
        print('tx: {} KB/s, rx: {} KB/s, cpu: {}%, mem: {}%, Time: {}'.format(tx, rx, cpu, mem, time.strftime('%H:%M:%S %Y-%m-%d', time.localtime())))

        message = {
            "tx": tx,
            "rx": rx,
            "cpu": cpu,
            "men": mem
        }
        mqttSender.send(message)
        sleep = config['interval'] - (time.time() - read_time)
        time.sleep(sleep if sleep > 0 else 0)

if __name__=="__main__":
    print('start!')
    file = open('./config.json', 'r')
    config = json5.load(file)
    file.close()
    
    checker = Checker(config['router'])
    mqttSender = MqttSender(config['thingsboard'])
    while True:
        try:
            mqttSender.start()
            checker.login()
            while (1 != 0):
                read_time = time.time()
                system_state = checker.get_system_state()
                ip_states = checker.get_ip_states()['result']

                tx = system_state['result'][1][0]['tx_bps']
                tx = round(tx / 1024, 2) # unit change to MB/s
                rx = system_state['result'][1][0]['rx_bps']
                rx = round(rx / 1024, 2)
                cpu = system_state['result'][2]['cpu']
                mem = system_state['result'][2]['mem']

                max_rxbps_ip_states = max(ip_states, key=lambda x: int(x['rx_bps']))
                max_rxbps_ip = max_rxbps_ip_states['addr']
                max_rxbps = int(max_rxbps_ip_states['rx_bps'])
                max_rxbps = round(max_rxbps / 1024, 2)
                print('tx: {:.2f} MB/s, rx: {:.2f} MB/s, cpu: {}%, mem: {}%, max_rxbps_ip: {}, max_rxbps: {}MB/s, Time: {}'.format(tx, rx, cpu, mem, max_rxbps_ip, max_rxbps, time.strftime('%H:%M:%S %Y-%m-%d', time.localtime())))

                message = {
                    "tx": tx,
                    "rx": rx,
                    "cpu": cpu,
                    "mem": mem,
                    "max_rxbps_ip": max_rxbps_ip,
                    "max_rxbps": max_rxbps
                }
                mqttSender.send(message)
                sleep = config['interval'] - (time.time() - read_time)
                time.sleep(sleep if sleep > 0 else 0)
        except KeyboardInterrupt:
            checker.logout()
            mqttSender.stop()
            print('End!')
            exit(1)
        except Exception as e:
            print(e)
            print(system_state)
            print(max_rxbps_ip_states)
            time.sleep(10)
            continue
    
    
        

    
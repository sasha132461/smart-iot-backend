import machine
import dht
import network
import ujson
from umqtt.simple import MQTTClient
import time
from ota import OTA, get_version

# -
class Configuration:
    def __init__(self, device_name: str, wifi_name: str, wifi_password: str,
                 mqtt_broker: str, mqtt_port: int, mqtt_username: str,
                 mqtt_password: str, mqtt_topic: str):
        self.device_name = device_name
        self.wifi_name = wifi_name
        self.wifi_password = wifi_password
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        self.mqtt_topic = mqtt_topic


def read_config() -> Configuration:
    try:
        with open('config.json', 'r') as f:
            config = ujson.load(f)
            return Configuration(
                config['device_name'],
                config['wifi']['ssid'],
                config['wifi']['password'],
                config['mqtt']['broker'],
                config['mqtt']['port'],
                config['mqtt']['username'],
                config['mqtt']['password'],
                config['mqtt']['topic']
            )
    except Exception as e:
        raise Exception("config.json error. Create or validate configuration file.", e)


def connect_wifi(name, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(name, password)

    while not wlan.isconnected():
        if wlan.status() == 1:
            print("Wi-Fi connecting...")
        elif wlan.status() == -3:
            raise Exception("Wi-Fi Connection rejected.")

        time.sleep(1)

    print("Connected to Wi-Fi:", wlan.ifconfig())


def connect_mqtt(device_id, mqtt_broker, mqtt_port, mqtt_username, mqtt_password):
    ssl_params = {'server_hostname': mqtt_broker}
    client = MQTTClient(
        client_id=device_id.encode(),
        server=mqtt_broker,
        port=mqtt_port,
        user=mqtt_username.encode(),
        password=mqtt_password.encode(),
        keepalive=60,
        ssl=True,
        ssl_params=ssl_params
    )

    try:
        client.connect()
        print("Connected to MQTT broker")
        return client
    except Exception as e:
        print("Could not connect to MQTT broker:", e)
        raise e


def read_battery_voltage():
    try:
        adc = machine.ADC(29)
        reading = adc.read_u16()
        voltage = (reading / 65535) * 3.3 * 3
        return voltage
    except Exception as e:
        print("Error reading battery voltage:", e)
        return None


def get_battery_percentage(voltage):
    if voltage is None:
        return None

    if voltage >= 4.2:
        return 100
    elif voltage <= 3.0:
        return 0
    else:
        return int(((voltage - 3.0) / (4.2 - 3.0)) * 100)


def check_ota():
    try:
        with open('config.json') as f:
            cfg = ujson.load(f)
        ota_cfg = cfg.get('ota', {})
        if ota_cfg.get('enabled') and ota_cfg.get('url'):
            ota = OTA(ota_cfg['url'], get_version())
            ota.update()
    except Exception as e:
        print(f"OTA error: {e}")


def start():
    configuration = read_config()

    connect_wifi(configuration.wifi_name, configuration.wifi_password)
    
    check_ota()

    mqtt_client = connect_mqtt(
        configuration.device_name,
        configuration.mqtt_broker,
        configuration.mqtt_port,
        configuration.mqtt_username,
        configuration.mqtt_password
    )

    sensor = dht.DHT22(machine.Pin(13))

    while True:
        try:
            battery_voltage = read_battery_voltage()
            battery_percent = get_battery_percentage(battery_voltage)

            sensor.measure()
            temp = sensor.temperature()

            payload = {
                "device_id": configuration.device_name,
                "temperature": temp,
                "battery_voltage": battery_voltage,
                "battery_percent": battery_percent,
                "timestamp": time.time()
            }

            mqtt_client.publish(configuration.mqtt_topic, ujson.dumps(payload))
            print("Published data:", payload)
        except Exception as e:
            print("Error:", e)

        time.sleep(10)

start()

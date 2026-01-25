import paho.mqtt.client as mqtt
import json
from dotenv import load_dotenv
import os
from redis_client import get_temperature_threshold
from influx_db import save_data

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = os.getenv("MQTT_PORT")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

TURN_RADIATOR_ON_COMMAND = 1
TURN_RADIATOR_OFF_COMMAND = 0

mqtt_client = None

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT Broker")
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to topic: {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}. Received {msg.payload.decode()}")

    try:
        data = json.loads(msg.payload.decode())
        current_temperature = data.get('temperature')
        battery_percentage = data.get('battery_percent')

        save_data(float(current_temperature), float(battery_percentage))

        if current_temperature is not None and current_temperature < get_temperature_threshold():
            relay_topic = "relay"
            client.publish(relay_topic, TURN_RADIATOR_ON_COMMAND)
            print(
                f"🌡️ Temperature {current_temperature}°C is below 22°C - Sending {TURN_RADIATOR_ON_COMMAND} to {relay_topic}")
        else:
            relay_topic = "relay"
            client.publish(relay_topic, TURN_RADIATOR_OFF_COMMAND)
            print(
                f"🌡️ Temperature {current_temperature}°C is ≥22°C - Sending {TURN_RADIATOR_OFF_COMMAND} to {relay_topic}")

    except json.JSONDecodeError:
        print("Failed to parse MQTT message as JSON")
    except Exception as e:
        print(f"Error processing MQTT message: {e}")


def start_mqtt_client():
    global mqtt_client

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.tls_set()

    print(f"Connecting to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}...")
    mqtt_client.connect(MQTT_BROKER, int(MQTT_PORT), 60)
    mqtt_client.loop_start()

    return mqtt_client


def stop_mqtt_client():
    global mqtt_client

    if mqtt_client is not None:
        print("Disconnecting from MQTT Broker...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


def get_mqtt_client():
    return mqtt_client

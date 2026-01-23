from fastapi import FastAPI
from pydantic import BaseModel
import paho.mqtt.client as mqtt
from contextlib import asynccontextmanager
import json
from dotenv import load_dotenv
import os

load_dotenv()

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = os.getenv("MQTT_PORT")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

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

        if current_temperature is not None and current_temperature < 22:
            relay_topic = "relay"
            # client.publish(relay_topic, 1)
            print(
                f"🌡️ Temperature {current_temperature}°C is below 22°C - Sending 1 to {relay_topic}")
        else:
            relay_topic = "relay"
            # client.publish(relay_topic, 0)
            print(
                f"🌡️ Temperature {current_temperature}°C is ≥22°C - Sending 0 to {relay_topic}")

    except json.JSONDecodeError:
        print("Failed to parse MQTT message as JSON")
    except Exception as e:
        print(f"Error processing MQTT message: {e}")


def on_disconnect(client, userdata, flags, reason_code, properties):
    print(f"Disconnected from MQTT Broker with result code: {reason_code}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_client
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    mqtt_client.tls_set()

    print(f"Connecting to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}...")
    mqtt_client.connect(MQTT_BROKER, int(MQTT_PORT), 60)
    mqtt_client.loop_start()

    yield

    # Shutdown: Disconnect from MQTT
    print("Disconnecting from MQTT Broker...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/temperature")
def read_temperature():
    return {"temperature": 10.5}


@app.put("/api/temperature/history")
def get_historical_temperature():
    pass


@app.get("/api/temperature/threshold")
def read_temperature_threshold():
    return {"threshold": 18}


@app.get("/api/battery")
def read_temperature_threshold():
    return {"battery_percentage": 75}


class TemperatureThresholdRequest(BaseModel):
    threshold: int


@app.put("/api/temperature/threshold")
def set_temperature_threshold(req: TemperatureThresholdRequest):
    pass


class ManualOverrideRequest(BaseModel):
    isManual: bool


@app.get("/api/manual-override")
def is_manual_override():
    return {"is_manual": True}


@app.put("/api/manual-override")
def set_manual_override(req: ManualOverrideRequest):
    pass


class RadiatorStateRequest(BaseModel):
    state: str  # "on" or "off"


@app.put("/api/radiator-state")
def set_radiator_state(req: RadiatorStateRequest):
    pass

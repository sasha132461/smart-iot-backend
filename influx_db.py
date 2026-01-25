import os
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

load_dotenv()

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")


def get_influxdb_client() -> InfluxDBClient:
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    print("✅ Connected to InfluxDB")
    return client


def save_data(temperature: float, battery_percentage: float):
    client = None
    try:
        client = get_influxdb_client()
        write_api = client.write_api(write_options=SYNCHRONOUS)

        if write_api:
            point = Point("dht11_sensor")
            point = point.field("temperature", temperature)
            point = point.field("battery_percentage", battery_percentage)

            point = point.time(datetime.utcnow())

            try:
                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
                print(
                    f"✅ Data persisted to InfluxDB - Temperature: {temperature}°C, Battery: {battery_percentage}%")
            except Exception as e:
                print(f"❌ Failed to write to InfluxDB: {e}")

        return None

    except Exception as e:
        print(f"Error fetching temperature from InfluxDB: {e}")
        return None
    finally:
        if client:
            client.close()


def get_last_temperature() -> Optional[Dict[str, Any]]:
    client = None
    try:
        client = get_influxdb_client()
        query_api = client.query_api()

        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -30d)
            |> filter(fn: (r) => r["_measurement"] == "dht11_sensor")
            |> filter(fn: (r) => r["_field"] == "temperature")
            |> last()
        '''

        tables = query_api.query(query, org=INFLUXDB_ORG)

        for table in tables:
            for record in table.records:
                return {
                    "temperature": record.get_value(),
                    "timestamp": record.get_time().isoformat() if record.get_time() else None
                }

        return None

    except Exception as e:
        print(f"Error fetching temperature from InfluxDB: {e}")
        return None
    finally:
        if client:
            client.close()


def get_last_battery() -> Optional[Dict[str, Any]]:
    client = None
    try:
        client = get_influxdb_client()
        query_api = client.query_api()

        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -30d)
            |> filter(fn: (r) => r["_measurement"] == "dht11_sensor")
            |> filter(fn: (r) => r["_field"] == "battery_percentage")
            |> last()
        '''

        tables = query_api.query(query, org=INFLUXDB_ORG)

        for table in tables:
            for record in table.records:
                return {
                    "battery_percentage": record.get_value(),
                    "timestamp": record.get_time().isoformat() if record.get_time() else None
                }

        return None

    except Exception as e:
        print(f"Error fetching battery from InfluxDB: {e}")
        return None
    finally:
        if client:
            client.close()


def get_temperature_history(limit: int = 100) -> list[Dict[str, Any]]:
    client = None
    try:
        client = get_influxdb_client()
        query_api = client.query_api()

        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -30d)
            |> filter(fn: (r) => r["_measurement"] == "dht11_sensor")
            |> filter(fn: (r) => r["_field"] == "temperature")
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: {limit})
        '''

        tables = query_api.query(query, org=INFLUXDB_ORG)

        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "temperature": record.get_value(),
                    "timestamp": record.get_time().isoformat() if record.get_time() else None
                })

        return results

    except Exception as e:
        print(f"Error fetching temperature history from InfluxDB: {e}")
        return []
    finally:
        if client:
            client.close()

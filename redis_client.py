import os
import redis
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    global _redis_client

    if _redis_client is None:
        redis_host = os.getenv("REDIS_HOST")
        redis_port = int(os.getenv("REDIS_PORT"))

        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
        )

        try:
            _redis_client.ping()
            print(f"✓ Connected to Redis at {redis_host}:{redis_port}")
        except redis.ConnectionError as e:
            print(f"✗ Failed to connect to Redis: {e}")
            _redis_client = None
            raise

    return _redis_client


def close_redis_client():
    global _redis_client

    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
        print("✓ Redis connection closed")


def set_manual_override(is_manual: bool) -> bool:
    try:
        client = get_redis_client()
        key = "manual_override"
        client.set(key, "1" if is_manual else "0")
        return True
    except Exception as e:
        print(f"Error setting manual override: {e}")
        return False


def get_manual_override() -> bool:
    try:
        client = get_redis_client()
        key = "manual_override"
        value = client.get(key)
        return value == "1" if value is not None else False
    except Exception as e:
        print(f"Error getting manual override: {e}")
        return False


def set_temperature_threshold(threshold: float) -> bool:
    try:
        client = get_redis_client()
        key = "temperature_threshold"
        client.set(key, str(threshold))
        return True
    except Exception as e:
        print(f"Error setting temperature threshold: {e}")
        return False


def get_temperature_threshold() -> float:
    try:
        client = get_redis_client()
        key = "temperature_threshold"
        value = client.get(key)
        return float(value) if value is not None else 20.0
    except Exception as e:
        print(f"Error getting temperature threshold: {e}")
        raise e


def set_radiator_state(state: str) -> bool:
    try:
        client = get_redis_client()
        key = "radiator_state"
        client.set(key, state)
        return True
    except Exception as e:
        print(f"Error setting radiator state: {e}")
        raise e


def get_radiator_state() -> str:
    try:
        client = get_redis_client()
        key = "radiator_state"
        value = client.get(key)
        return value if value is not None else "off"
    except Exception as e:
        print(f"Error getting radiator state: {e}")
        raise e

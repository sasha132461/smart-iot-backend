from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from influx_db import get_last_temperature, get_temperature_history, get_last_battery
from mqtt_client import turn_radiator_on, turn_radiator_off
from redis_client import (
    fetch_manual_override,
    save_manual_override,
    fetch_temperature_threshold,
    save_temperature_threshold,
    fetch_radiator_state,
    save_radiator_state,
)

router = APIRouter()


@router.get("/api/temperature")
def read_temperature():
    result = get_last_temperature()

    if result is None:
        raise HTTPException(status_code=404, detail="No temperature data found")

    return {"temperature": result["temperature"]}


@router.get("/api/temperature/history")
def get_historical_temperature():
    results = get_temperature_history(limit=100)

    if not results:
        raise HTTPException(status_code=404, detail="No temperature history found")

    return {"history": results}


@router.get("/api/temperature/threshold")
def read_temperature_threshold():
    threshold = fetch_temperature_threshold()

    return {"threshold": threshold}


@router.get("/api/battery")
def read_battery():
    result = get_last_battery()

    if result is None:
        raise HTTPException(status_code=404, detail="No battery data found")

    return {"battery_percentage": result["battery_percentage"]}


class TemperatureThresholdRequest(BaseModel):
    threshold: float


@router.put("/api/temperature/threshold")
def set_temperature_threshold(req: TemperatureThresholdRequest):
    success = save_temperature_threshold(req.threshold)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to set temperature threshold")

    return {"threshold": req.threshold, "message": "Temperature threshold updated successfully"}


class ManualOverrideRequest(BaseModel):
    is_manual: bool


@router.get("/api/manual-override")
def is_manual_override():
    is_manual = fetch_manual_override()
    return {"is_manual": is_manual}


@router.put("/api/manual-override")
def set_manual_override(req: ManualOverrideRequest):
    success = save_manual_override(req.is_manual)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to set manual override state")

    return {"is_manual": req.is_manual}


class RadiatorStateRequest(BaseModel):
    state: str  # "on" or "off"


@router.get("/api/radiator-state")
def get_radiator_state_endpoint():
    is_manual = fetch_manual_override()

    if is_manual:
        state = fetch_radiator_state()

        if state is None:
            raise HTTPException(status_code=404, detail="No radiator state found")

        return {"state": state}
    else:
        threshold = fetch_temperature_threshold()
        temperature = get_last_temperature()

        return {"state": "on" if temperature["temperature"] < threshold else "off"}


@router.put("/api/radiator-state")
def set_radiator_state(req: RadiatorStateRequest):
    if req.state not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="State must be 'on' or 'off'")

    is_manual = fetch_manual_override()
    if not is_manual:
        raise HTTPException(
            status_code=403,
            detail="Manual override must be enabled to control the radiator"
        )

    success = save_radiator_state(req.state)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to set radiator state")

    # todo notify radiator controller of state change
    if req.state == "on":
        turn_radiator_on()
    else:
        turn_radiator_off()

    return {"state": req.state}

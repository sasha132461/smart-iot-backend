from fastapi import FastAPI
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from mqtt_client import start_mqtt_client, stop_mqtt_client
from api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_mqtt_client()

    yield

    stop_mqtt_client()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

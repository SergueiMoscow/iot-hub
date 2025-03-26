from app.mqtt.mqtt_client import start_mqtt_client, stop_mqtt_client
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаем MQTT-клиент
    app.state.mqtt_client = await start_mqtt_client()
    yield
    # Останавливаем MQTT-клиент при завершении
    await stop_mqtt_client(app.state.mqtt_client)

# app/mqtt/mqtt_client.py
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional

import aiomqtt
from fastapi import FastAPI, Depends

from app.core.config import settings
from app.core.setup_logger import setup_logger
from app.mqtt.mqtt_messages import handle_message

logger = setup_logger(__name__)

class MQTTClientManager:
    def __init__(self):
        self.client: Optional[aiomqtt.Client] = None
        self._should_stop = asyncio.Event()

    def create_client(self) -> aiomqtt.Client:
        return aiomqtt.Client(
            hostname=settings.RABBITMQ_HOST,
            port=int(settings.RABBITMQ_PORT),
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD,
        )

    async def start(self):
        try:
            self.client = self.create_client()
            async with self.client:
                logger.info("Connected to MQTT Broker!")
                await self.client.subscribe(settings.TOPIC)
                logger.info(f"Subscribed to topic: {settings.TOPIC}")
                async for message in self.client.messages:
                    if self._should_stop.is_set():
                        break
                    await handle_message(self.client, message)
        except aiomqtt.MqttError as e:
            logger.error(f"MQTT error: {e}")
        except Exception as e:
            logger.error(f"Client error: {e}")

    async def stop(self):
        self._should_stop.set()
        if self.client:
            self.client = None
            logger.info("MQTT client stopped")

    async def send_mqtt_message(self, topic: str, payload: str | dict):
        if not self.client:
            raise RuntimeError("MQTT client is not initialized")
        try:
            message = json.dumps(payload) if isinstance(payload, dict) else payload
            await self.client.publish(topic, message)
            logger.info(f"Message published to {topic}: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = MQTTClientManager()
    app.state.mqtt_manager = manager
    task = asyncio.create_task(manager.start())

    try:
        yield
    finally:
        await manager.stop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        logger.info("Lifespan shutdown complete")

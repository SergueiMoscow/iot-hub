import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from typing import Optional

import aiomqtt
from fastapi import FastAPI

from app.core.config import settings
from app.core.setup_logger import setup_logger
from app.mqtt.mqtt_messages import handle_message

logger = setup_logger(__name__)

# Константы для переподключения
RECONNECT_CONFIG = {
    "first_delay": 1,
    "rate": 2,
    "max_count": 12,
    "max_delay": 60
}


class MQTTClientManager:
    def __init__(self):
        self.client: Optional[aiomqtt.Client] = None
        self.thread: Optional[threading.Thread] = None
        self._should_stop = threading.Event()  # Флаг для остановки
        self.mqtt_loop: Optional[asyncio.AbstractEventLoop] = None
        self._client_task: Optional[asyncio.Task] = None  # Для хранения задачи клиента


    async def on_connect(self):
        logger.info("Connected to MQTT Broker!")

    async def on_disconnect(self):
        logger.info("Disconnected from MQTT Broker!")
        await self.reconnect()

    async def reconnect(self):
        reconnect_count, reconnect_delay = 0, RECONNECT_CONFIG["first_delay"]

        while reconnect_count < RECONNECT_CONFIG["max_count"]:
            logger.info(f"Reconnecting in {reconnect_delay} seconds...")
            await asyncio.sleep(reconnect_delay)

            try:
                async with self.create_client() as client:
                    self.client = client
                    logger.info("Reconnected successfully!")
                    return client
            except Exception as err:
                logger.error(f"Reconnect failed: {err}")

            reconnect_delay = min(reconnect_delay * RECONNECT_CONFIG["rate"],
                                  RECONNECT_CONFIG["max_delay"])
            reconnect_count += 1

        logger.error(f"Reconnect failed after {reconnect_count} attempts. Exiting...")

    def create_client(self) -> aiomqtt.Client:
        return aiomqtt.Client(
            hostname=settings.RABBITMQ_HOST,
            port=int(settings.RABBITMQ_PORT),
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD,
        )

    async def subscribe(self, client: aiomqtt.Client):
        await client.subscribe(settings.TOPIC)
        logger.info(f"Subscribed to topic: {settings.TOPIC}")

    async def message_handler(self, client: aiomqtt.Client):
        while not self._should_stop.is_set():  # Проверяем флаг остановки
            try:
                async for message in client.messages:
                    if self._should_stop.is_set():
                        break
                    await handle_message(client, message)
                    # logger.info(f"Received message: {message}")
            except aiomqtt.MqttError as e:
                if self._should_stop.is_set():
                    break
                logger.error(f"MQTT error: {e}")
                await asyncio.sleep(RECONNECT_CONFIG["first_delay"])
                await self.on_disconnect()

    async def start(self):
        self._should_stop.clear()
        try:
            async with self.create_client() as client:
                self.client = client
                await self.on_connect()
                await self.subscribe(client)
                await self.message_handler(client)
        except Exception as e:
            logger.error(f"MQTT client error: {e}")
        finally:
            self.client = None

    def run_in_thread(self):
        self.mqtt_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.mqtt_loop)
        try:
            self._client_task = self.mqtt_loop.create_task(self.start())
            self.mqtt_loop.run_until_complete(self._client_task)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"MQTT thread error: {e}")
        finally:
            if self.mqtt_loop.is_running():
                self.mqtt_loop.close()
            self.mqtt_loop = None

    async def stop(self):
        """Корректная остановка клиента"""
        self._should_stop.set()

        if self.client:
            # Просто завершаем контекстный менеджер (автоматически закроет соединение)
            # Для этого прерываем работу message_handler
            pass

        if self.mqtt_loop and self._client_task:
            # Отменяем основную задачу клиента
            self._client_task.cancel()
            try:
                await asyncio.wait_for(self._client_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = MQTTClientManager()
    manager.thread = threading.Thread(target=manager.run_in_thread, daemon=True)
    manager.thread.start()

    try:
        yield {"mqtt_manager": manager}  # Возвращаем словарь с менеджером
        # await manager.stop()
    finally:
        # Корректная остановка
        if manager.thread:
            if manager.mqtt_loop:
                future = asyncio.run_coroutine_threadsafe(manager.stop(), manager.mqtt_loop)
                try:
                    future.result(timeout=2)
                except Exception as e:
                    logger.error(f"Error stopping MQTT client: {e}")

            manager.thread.join(timeout=1)

            if manager.thread.is_alive():
                logger.warning("MQTT thread did not stop gracefully")

import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
import aiomqtt
import asyncio

from app.core.config import settings
from app.core.setup_logger import setup_logger
from app.mqtt.mqtt_messages import handle_message

mqtt_client = None
mqtt_thread = None

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60
logger = setup_logger(__name__)

async def on_connect(client):
    logger.info("Connected to MQTT Broker!")

async def on_disconnect(client):
    logger.info("Disconnected from MQTT Broker!")
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logger.info(f"Reconnecting in {reconnect_delay} seconds...")
        await asyncio.sleep(reconnect_delay)
        try:
            async with aiomqtt.Client(
                hostname=settings.RABBITMQ_HOST,
                port=int(settings.RABBITMQ_PORT),
                username=settings.RABBITMQ_USER,
                password=settings.RABBITMQ_PASSWORD,
            ) as client:
                logger.info("Reconnected successfully!")
                return client
        except Exception as err:
            logger.error(f"Reconnect failed: {err}")
        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logger.error(f"Reconnect failed after {reconnect_count} attempts. Exiting...")

async def connect_mqtt():
    global mqtt_client
    async with aiomqtt.Client(
        hostname=settings.RABBITMQ_HOST,
        port=int(settings.RABBITMQ_PORT),
        username=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD,
    ) as client:
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        mqtt_client = client
        yield client

async def subscribe(client: aiomqtt.Client):
    await client.subscribe(settings.TOPIC)
    logger.info(f"Subscribed to topic: {settings.TOPIC}")

async def message_handler(client: aiomqtt.Client):
    while True:
        try:
            async for message in client.messages:
                await handle_message(client, message)
                logger.info(f"Received message: {message}")
        except aiomqtt.MqttError as e:
            logger.error(f"MQTT error: {e}")
            await asyncio.sleep(FIRST_RECONNECT_DELAY)
            await on_disconnect(client)

async def start_mqtt_client():
    async for client in connect_mqtt():
        await subscribe(client)
        await message_handler(client)
        logger.info("MQTT client started.")
        return client

# async def stop_mqtt_client(client: aiomqtt.Client):
#     await client.disconnect()
#     logger.info("MQTT client disconnected.")

def run_mqtt_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_mqtt_client())

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_thread
    mqtt_thread = threading.Thread(target=run_mqtt_client)
    mqtt_thread.start()
    yield
    # await stop_mqtt_client(mqtt_client)
    mqtt_thread.join()

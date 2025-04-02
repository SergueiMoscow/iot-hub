import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.setup_logger import setup_logger
from app.mqtt.mqtt_messages import on_message
from paho.mqtt import client as paho_mqtt_client
from paho.mqtt.enums import CallbackAPIVersion


mqtt_client = None

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60
logger = setup_logger(__name__)

def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
        else:
            logger.error(f"Failed to connect, return code {rc}")
            if rc == 5:
                logger.error("Authentication error. Check username/password.")
            elif rc == 1:
                logger.error("Connection refused - incorrect protocol version.")
            elif rc == 4:
                logger.error("Connection refused - bad credentials.")

    client = paho_mqtt_client.Client(CallbackAPIVersion.VERSION2)
    client.username_pw_set(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    try:
        client.connect(host=settings.RABBITMQ_HOST, port=int(settings.RABBITMQ_PORT), keepalive=60)
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise

    client.loop_start()
    return client


def on_disconnect(client, userdata, rc, properties, *args):
    logger.info(f"Disconnected with result code: {rc}")
    # Проверяем, инициировано ли отключение вручную (rc == 0)
    if rc != 0:  # Если это неявное отключение, пытаемся переподключиться
        reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
        while reconnect_count < MAX_RECONNECT_COUNT:
            logger.info(f"Reconnecting in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)
            try:
                client.reconnect()
                logger.info("Reconnected successfully!")
                return
            except Exception as err:
                logger.error(f"Reconnect failed: {err}")
            reconnect_delay *= RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
            reconnect_count += 1
        logger.error(f"Reconnect failed after {reconnect_count} attempts. Exiting...")


def subscribe(client: paho_mqtt_client.Client):
    # def on_message(client, userdata, msg):
    #     logger.info(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(settings.TOPIC)
    client.on_message = on_message
    logger.info(f"Subscribed to topic: {settings.TOPIC}")


async def start_mqtt_client():
    client = connect_mqtt()
    subscribe(client)
    return client


async def stop_mqtt_client(client: paho_mqtt_client.Client):
    client.loop_stop()
    client.disconnect()
    logger.info("MQTT client disconnected.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_client
    mqtt_client = await start_mqtt_client()
    yield
    await stop_mqtt_client(mqtt_client)
import json
from datetime import datetime
import pytz
from app.api.deps import SessionDep
from app.core.db import engine
from sqlmodel import Session
from app.core.config import settings
from app.core.setup_logger import setup_logger
from app.models.device_data import DeviceData
from paho.mqtt import client as mqtt_client
from services.utils import is_json

# from smarthub.db.models import DeviceData

logger = setup_logger(__name__)
def handle_gettime(client: mqtt_client.Client, topic: str):
    """
    Отправляет текущее время устройству в ответ на запрос.
    """
    # Формируем топик для ответа
    response_topic = topic.replace("/gettime", "/set/time")

    # Получаем текущее время
    timezone = pytz.timezone("Europe/Moscow")
    current_time = datetime.now(timezone)

    # Формируем ответ в JSON
    time_data = {
        "abbreviation": "MSK",
        "client_ip": "0.0.0.0",  # Можно оставить заглушку
        "datetime": current_time.isoformat(),
        "day_of_week": str(current_time.weekday() + 1),  # 1-7 (понедельник-воскресенье)
        "day_of_year": str(current_time.timetuple().tm_yday),
        "dst": False,
        "dst_from": None,
        "dst_offset": 0,
        "dst_until": None,
        "raw_offset": 10800,
        "timezone": "Europe/Moscow",
        "unixtime": int(current_time.timestamp()),
        "utc_datetime": current_time.astimezone(pytz.utc).isoformat(),
        "utc_offset": "+03:00",
        "week_number": str(current_time.isocalendar()[1]),
    }

    # Отправляем ответ устройству
    client.publish(response_topic, json.dumps(time_data))
    logger.info(f"Sent time data to {response_topic}")


def on_message(client: mqtt_client.Client, userdata, msg):
    """
    Обрабатывает входящие сообщения.
    """
    topic = msg.topic
    payload = msg.payload.decode()

    # Если запрос на получение времени
    if topic.endswith("/gettime"):
        handle_gettime(client, topic)
    else:
        # Логируем и сохраняем сообщение в базу данных
        logger.info(f"Received `{payload}` from `{topic}` topic")
        if is_json(payload):
            save_to_db(topic, payload)


def subscribe(client: mqtt_client.Client):
    """
    Подписывается на топик и настраивает обработчик сообщений.
    """
    client.subscribe(settings.TOPIC)
    client.on_message = on_message
    logger.info(f"Subscribed to topic: {settings.TOPIC}")


def save_to_db(topic: str, payload: str):
    """
    Сохраняет сообщение в базу данных.
    """
    parts = topic.split("/")
    if len(parts) < 4:
        logger.error(f"Invalid topic format: {topic}")
        return

    object_, room, device, state, *module = parts
    module = "/".join(module) if module else ""
    try:
        payload_dict = json.loads(payload)
        value = json.dumps(payload_dict)  # Сохраняем весь JSON как строку
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode payload: {e}")
        return
    message = DeviceData(
        object=object_,
        room=room,
        device=device,
        state=state,
        module=module,
        value=value,
        timestamp=datetime.now()
    )
    with Session(engine) as session:
        try:
            session.add(message)
            session.commit()
            session.refresh(message)
            logger.info(f"Saved message to DB: {message.id}")
        except Exception as e:
            logger.error(f"Failed to save message to DB: {e}")
            session.rollback()
        finally:
            session.close()

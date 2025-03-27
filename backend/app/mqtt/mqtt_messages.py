import json
import secrets
from datetime import datetime
import pytz
from app.core.db import engine
from sqlmodel import Session
from app.core.config import settings
from app.core.setup_logger import setup_logger
from app.models.device_data import DeviceData
from paho.mqtt import client as mqtt_client

from app.models.device_file_request import DeviceFileRequest
from services.utils import is_json

logger = setup_logger(__name__)

def handle_startup(client: mqtt_client.Client, topic: str, payload: str):
    '''
    Обрабатывает сообщение /startup и отправляет команду на получение файла.
    '''
    try:
        payload_dict = json.loads(payload)
        device_ip = payload_dict.get('IP')
        device_topic = payload_dict.get('topic', topic.rsplit('/', 1)[0]).rstrip('/')  # Убираем слэш
        online_time = payload_dict.get('online')
    except json.JSONDecodeError as e:
        logger.error(f'Failed to decode startup payload: {e}')
        return

    secret_key = secrets.token_hex(16)
    send_file_topic = f'{device_topic}/set/sendFile'.replace('//', '/')
    api_url = (
        f'{settings.APP_SCHEME}://'
        f'{settings.APP_HOST}:{settings.APP_PORT}'
        f'{settings.API_V1_STR}/mqtt/upload-file'
    )

    send_file_message = {
        'filename': 'devices.json',
        'url': api_url,
        'secret_key': secret_key,
    }

    client.publish(send_file_topic, json.dumps(send_file_message))
    logger.info(f'Sent sendFile command to {send_file_topic}')

    with Session(engine) as session:
        try:
            request = DeviceFileRequest(
                topic=device_topic,  # Уже без слэша
                secret_key=secret_key,
                requested_at=datetime.now(pytz.utc),
                filename=send_file_message['filename'],
            )
            session.add(request)
            session.commit()
            logger.info(f'Saved file request for {device_topic} with secret_key: {secret_key}')
        except Exception as e:
            logger.error(f'Failed to save file request: {e}')
            session.rollback()


def handle_gettime(client: mqtt_client.Client, topic: str):
    """
    Отправляет текущее время устройству в ответ на запрос.
    """
    # Формируем топик для ответа
    response_topic = topic.replace('/gettime', '/set/time')

    # Получаем текущее время
    timezone = pytz.timezone('Europe/Moscow')
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
    elif topic.endswith("/startup"):
        logger.info(f"Received `{payload}` from `{topic}` topic")
        handle_startup(client, topic, payload)
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

import json
import secrets
from datetime import datetime
import pytz
from app.core.db import engine
from sqlmodel import Session
from app.core.config import settings
from app.core.setup_logger import setup_logger
from app.models.controller_board import create_or_update_controller_board
from app.models.controller_file_request import ControllerFileRequest
from app.services.process_messages import process_state_message
from app.services.utils import is_json
import aiomqtt

logger = setup_logger(__name__)

async def request_file_from_controller(client: aiomqtt.Client, device_topic: str, filename: str):
    """
    Формирует сообщение для запроса файла и регистрирует его в таблице ControllerFileRequest.
    """
    secret_key = secrets.token_hex(16)
    send_file_topic = f'{device_topic}/set/sendFile'.replace('//', '/')
    api_url = (
        f'{settings.APP_SCHEME}://'
        f'{settings.APP_HOST}:{settings.APP_PORT}'
        f'{settings.API_V1_STR}/mqtt/upload-file'
    )

    send_file_message = {
        'filename': filename,
        'url': api_url,
        'secret_key': secret_key,
    }

    await client.publish(send_file_topic, json.dumps(send_file_message))
    logger.info(f'Sent sendFile command to {send_file_topic}')

    with Session(engine) as session:
        try:
            request = ControllerFileRequest(
                topic=device_topic,
                secret_key=secret_key,
                requested_at=datetime.now(pytz.utc),
                filename=filename,
            )
            session.add(request)
            session.commit()
            logger.info(f'Saved file request for {device_topic} with secret_key: {secret_key}')
        except Exception as e:
            logger.error(f'Failed to save file request: {e}')
            session.rollback()


async def handle_startup(client: aiomqtt.Client, topic: str, payload: str):
    '''
    Обрабатывает сообщение /startup и отправляет команду на получение файлов.
    '''
    try:
        payload_dict = json.loads(payload)
        device_ip = payload_dict.get('IP')
        device_topic = payload_dict.get('topic', topic.rsplit('/', 1)[0]).rstrip('/')  # Убираем слэш
        online_time = payload_dict.get('online')
    except json.JSONDecodeError as e:
        logger.error(f'Failed to decode startup payload: {e}')
        return

    # Запрашиваем два файла: devices.json и mqtt.json
    await request_file_from_controller(client, device_topic, 'devices.json')
    await request_file_from_controller(client, device_topic, 'mqtt.json')

    # Регистрируем в таблице модели ControllerBoard
    with Session(engine) as session:
        await create_or_update_controller_board(
            session=session,
            topic=device_topic,
            ip=device_ip,
            online_time=online_time
        )


async def handle_gettime(client: aiomqtt.Client, topic: str):
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
    await client.publish(response_topic, json.dumps(time_data))
    logger.info(f"Sent time data to {response_topic}")


async def handle_message(client: aiomqtt.Client, message):
    """
    Обрабатывает входящие сообщения.
    """
    topic = str(message.topic)
    payload = message.payload.decode()

    # Если запрос на получение времени
    if topic.endswith("/gettime"):
        await handle_gettime(client, topic)
    elif topic.endswith("/startup"):
        logger.info(f"Received `{payload}` from `{topic}` topic")
        await handle_startup(client, topic, payload)
    else:
        # Логируем и сохраняем сообщение в базу данных
        logger.info(f"Received `{payload}` from `{topic}` topic")
        if is_json(payload):
            # save_to_db(topic, payload)
            process_state_message(payload=payload, topic=topic)


# def save_to_db(topic: str, payload: str):
#     """
#     Сохраняет сообщение в базу данных.
#     """
#     parts = topic.split("/")
#     if len(parts) < 4:
#         logger.error(f"Invalid topic format: {topic}")
#         return
#
#     object_, room, device, state, *module = parts
#     module = "/".join(module) if module else ""
#     try:
#         payload_dict = json.loads(payload)
#         value = json.dumps(payload_dict)  # Сохраняем весь JSON как строку
#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to decode payload: {e}")
#         return
#     message = DeviceData(
#         object=object_,
#         room=room,
#         device=device,
#         state=state,
#         module=module,
#         value=value,
#         timestamp=datetime.now()
#     )
#     with Session(engine) as session:
#         try:
#             session.add(message)
#             session.commit()
#             session.refresh(message)
#             logger.info(f"Saved message to DB: {message.id}")
#         except Exception as e:
#             logger.error(f"Failed to save message to DB: {e}")
#             session.rollback()
#         finally:
#             session.close()

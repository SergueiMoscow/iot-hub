# backend/app/api/routes/board.py
import json
import os
from fastapi import APIRouter, HTTPException, UploadFile, Form
from sqlmodel import Session, select
from app.api.deps import SessionDep, AsyncSessionDep
from app.core.db import engine, AsyncSession
from app.models.controller_board import ControllerBoard
from app.models.controller_file_request import ControllerFileRequest
from app.repositories.controller_board_repository import get_controller_by_topic, create_or_update_controller_board
from app.repositories.controller_file_request_repository import get_controller_file_request_by_topic_and_secret_key
from app.services.get_active_mqtt_config import get_active_mqtt_config
from app.services.process_startup_message import process_startup_message

router = APIRouter(prefix='/mqtt', tags=['mqtt'])

def save_file_to_disk(topic: str, file: UploadFile) -> str:
    '''
    Сохраняет файл на диск в директорию devices/<topic>/.
    '''
    sanitized_topic = topic.replace('/', '_')
    directory = f'devices/{sanitized_topic}'
    os.makedirs(directory, exist_ok=True)
    file_path = f'{directory}/{file.filename}'

    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    return file_path


@router.post('/upload-file', dependencies=None)
async def upload_file(
    session: AsyncSessionDep,
    topic: str = Form(...),
    secret_key: str = Form(...),
    file: UploadFile = Form(...),
) -> dict[str, str]:
    '''
    Принимает файл от устройства через POST-запрос.
    '''
    # Проверяем secret_key и topic
    controller_file_request = await get_controller_file_request_by_topic_and_secret_key(
        session=session,
        topic=topic,
        secret_key=secret_key,
    )

    controller_board = await get_controller_by_topic(session=session, topic=topic)

    if not controller_file_request:
        raise HTTPException(status_code=403, detail='Invalid topic or secret_key')

    # Проверяем, что загруженный файл соответствует запрошенному
    if file.filename != controller_file_request.filename:
        raise HTTPException(status_code=400, detail='File does not match requested filename')

    file_path = save_file_to_disk(topic, file)

    if file.filename == 'mqtt.json':
        mqtt_config = get_active_mqtt_config(file_path)
        await create_or_update_controller_board(
            session=session,
            topic=topic,
            rabbitmq_user=mqtt_config['User'],
            period=mqtt_config['Period'],
        )
    elif file.filename == 'devices.json':
        with open(file_path, 'r') as f:
            devices_json = json.load(f)
        await process_startup_message(session=session, devices=devices_json, controller_id=controller_board.id)
    return {'message': f'File saved to {file_path}'}

# backend/app/api/routes/board.py
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, File
from sqlmodel import Session, select
from app.api.deps import SessionDep
from app.core.db import engine
from app.models.controller_board import ControllerBoard, create_or_update_controller_board
from app.models.controller_file_request import ControllerFileRequest
from app.core.config import settings
from app.services.get_active_mqtt_config import get_active_mqtt_config

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
    session: SessionDep,
    topic: str = Form(...),
    secret_key: str = Form(...),
    file: UploadFile = Form(...),
) -> dict[str, str]:
    '''
    Принимает файл от устройства через POST-запрос.
    '''
    # Проверяем secret_key и topic
    statement = select(ControllerFileRequest).where(
        ControllerFileRequest.topic == topic,
        ControllerFileRequest.secret_key == secret_key
    )
    request = session.exec(statement).first()

    if not request:
        raise HTTPException(status_code=403, detail='Invalid topic or secret_key')

    # Проверяем, что загруженный файл соответствует запрошенному
    if file.filename != request.filename:
        raise HTTPException(status_code=400, detail='File does not match requested filename')

    file_path = save_file_to_disk(topic, file)

    if file.filename == 'mqtt.json':
        mqtt_config = get_active_mqtt_config(file_path)
        with Session(engine) as session:
            await create_or_update_controller_board(
                session=session,
                topic=topic,
                rabbitmq_user=mqtt_config['User'],
                period=mqtt_config['Period'],
            )
    return {'message': f'File saved to {file_path}'}

# backend/app/api/routes/board.py
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, File
from sqlmodel import Session, select
from app.api.deps import SessionDep
from app.models.controller_file_request import ControllerFileRequest
from app.core.config import settings

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
    Принимает файл devices.json от устройства через POST-запрос.
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
    return {'message': f'File saved to {file_path}'}

import json

from fastapi import APIRouter, Depends
from sqlmodel import select

from app.api.deps import get_current_user, SessionDep
from app.main import app
from app.models.board import Board

router = APIRouter(tags=['dashboard'])

@router.get('/boards', dependencies=[Depends(get_current_user)])
async def get_boards(session: SessionDep) -> list[dict]:
    boards = session.exec(select(Board)).all()
    return [{'topic': b.topic, 'ip': b.ip, 'is_online': b.is_online, 'last_seen': b.last_seen} for b in boards]


@router.post('/boards/{topic}/relay/{name}')
async def toggle_relay(topic: str, name: str, state: str, session: SessionDep):
    # Отправка команды через MQTT в топик topic/set/relay
    app.state.mqtt_client.publish(f'{topic}/set/relay', json.dumps({'name': name, 'state': state}))
    return {'message': f'Relay {name} set to {state}'}

# backend/app/api/routes/boards.py
import json
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from sqlmodel import func, select

from app.api.deps import get_current_user, SessionDep, MqttClientDep, CurrentUser
from app.models.controller_board import ControllerBoard, ControllerBoardPublic, ControllerBoardsPublic

router = APIRouter(tags=['ControllerBoards'])

@router.get('/boards', dependencies=[Depends(get_current_user)], response_model=ControllerBoardsPublic)
async def get_boards(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(ControllerBoard)
        count = session.exec(count_statement).one()
        statement = select(ControllerBoard).offset(skip).limit(limit)
        items = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(ControllerBoard)
            # .where(ControllerBoard.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(ControllerBoard)
            # .where(ControllerBoard.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        items = session.exec(statement).all()

    return ControllerBoardsPublic(data=items, count=count)


@router.post('/boards/{topic}/relay/{name}')
async def toggle_relay(
    topic: str,
    name: str,
    state: str,
    session: SessionDep,
    mqtt_client: MqttClientDep,
    current_user: CurrentUser,
):
    mqtt_client.publish(f'{topic}/set/relay', json.dumps({'name': name, 'state': state}))
    return {'message': f'Relay {name} set to {state}'}

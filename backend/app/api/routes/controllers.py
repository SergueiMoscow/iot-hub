# backend/app/api/routes/boards.py
import json
import logging
import time
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import func, select

from app.api.dep_mqtt_client import get_mqtt_manager
from app.api.deps import get_current_user, SessionDep, CurrentUser, AsyncSessionDep
from app.models import Device
from app.models.controller_board import ControllerBoard, ControllerBoardsPublic
from app.models.device_state import DeviceStatePublic, DeviceState, DeviceStatesPublic
from app.mqtt.mqtt_client import MQTTClientManager
from app.repositories.controller_board_repository import get_controller_by_id

router = APIRouter(tags=['ControllerBoards'])
logger = logging.getLogger(__name__)

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


@router.get("/controller_state/{id}", response_model=DeviceStatesPublic)
def get_controller_state(id: int, session: SessionDep):
    controller = session.get(ControllerBoard, id)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")

    device_states = session.exec(
        select(DeviceState).join(Device).where(Device.controller_id == id)
    ).all()

    public_states = [DeviceStatePublic.from_db_state(state) for state in device_states]
    return DeviceStatesPublic(data=public_states, count=len(public_states))


@router.post('/boards/{id}/relay/{name}')
async def toggle_relay(
    id: int,
    name: str,
    state: str,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    mqtt_manager: MQTTClientManager = Depends(get_mqtt_manager),
):
    controller = await get_controller_by_id(session=session, id=id)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")
    topic = controller.topic
    try:
        start_time = time.time()
        await mqtt_manager.send_mqtt_message(topic + f'/set/{name}', state)
        execution_time = time.time() - start_time
        logger.info(f"Toggle relay execution time: {execution_time:.4f} seconds")
        return {
            'message': f'Relay {name} set to {state}',
            'execution_time': execution_time
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"MQTT client not connected: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to send MQTT command: {str(e)}")

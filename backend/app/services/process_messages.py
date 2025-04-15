import json
import logging

from app.core.db import AsyncSession
# from sqlmodel.ext.asyncio.session import AsyncSession

# from app.core.db import async_engine
from app.repositories.controller_board_repository import get_controller_by_topic
from app.repositories.device_repository import get_device_by_name_and_controller_id, \
    get_device_type_by_name_and_controller_id
from app.repositories.device_state_repository import update_or_create_device_state_by_device_id
from app.services.history_services import save_to_history

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def process_state_message(payload: dict, topic: str):
    async with AsyncSession() as session:
    # with Session(engine) as session:
        controller = await get_controller_by_topic(session=session, topic=topic)
        if not controller:
            logger.error(f"Controller with topic {topic} not found")
            return

        for device_name, state in payload.items():
            device_type = await get_device_type_by_name_and_controller_id(session=session, device_name=device_name, controller_id=controller.id)
            if device_name == 'time':
                continue

            if not device_type:
                logger.error(f"Device {device_name} not found for controller {controller.id}")
                continue
            value = json.dumps(state)
            if device_type == 'Relay':
                device = await get_device_by_name_and_controller_id(
                    session=session,
                    device_name=device_name,
                    controller_id=controller.id
                )
                value = 1 if state =='on' else 0
                device_state = await update_or_create_device_state_by_device_id(
                    session=session,
                    device_id=device.id,
                    value=value,
                )

            elif device_type == 'DS18B20':
                for parameter, value in state.items():
                    parameter = parameter
                    value = value
                    device = await get_device_by_name_and_controller_id(
                        session=session,
                        device_name=device_name,
                        controller_id=controller.id,
                        extra_name=parameter,
                    )
                    device_state = await update_or_create_device_state_by_device_id(
                        session=session,
                        device_id=device.id,
                        value=value,
                        parameter=parameter,
                    )
            elif device_type == 'DHT':
                parameter = 'temperature'
                value = state['temperature']
                device = await get_device_by_name_and_controller_id(
                    session=session,
                    device_name=device_name,
                    controller_id=controller.id,
                    extra_name=parameter,
                )
                device_state = await update_or_create_device_state_by_device_id(
                    session=session,
                    device_id=device.id,
                    value=value,
                    parameter=parameter,
                )
                parameter = 'humidity'
                value = state['humidity']
                device = await get_device_by_name_and_controller_id(
                    session=session,
                    device_name=device_name,
                    controller_id=controller.id,
                    extra_name=parameter,
                )
                device_state = await update_or_create_device_state_by_device_id(
                    session=session,
                    device_id=device.id,
                    value=value,
                    parameter=parameter,
                )
            elif device_type.startswith('MQ'):
                parameter = 'gas_raw'
                value = state['gas_raw']
                device = await get_device_by_name_and_controller_id(
                    session=session,
                    device_name=device_name,
                    controller_id=controller.id,
                    extra_name=parameter,
                )
                device_state = await update_or_create_device_state_by_device_id(
                    session=session,
                    device_id=device.id,
                    value=value,
                    parameter=parameter,
                )
                parameter = 'gas_ppm'
                value = state['gas_ppm']
                device = await get_device_by_name_and_controller_id(
                    session=session,
                    device_name=device_name,
                    controller_id=controller.id,
                    extra_name=parameter,
                )
                device_state = await update_or_create_device_state_by_device_id(
                    session=session,
                    device_id=device.id,
                    value=value,
                    parameter=parameter,
                )
            # Update DeviceState
            else:
                logger.error(f"Unknown device type {device.type}")
            continue

            # Update DeviceHistory
            # await save_to_history(
            #     session=session,
            #     device=device,
            #     data=payload,
            # )

        await session.commit()

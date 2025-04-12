from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models import DeviceState, Device


async def get_device_state_by_device_id(session: AsyncSession, device_id: int) -> DeviceState | None:
    result = await session.scalars(select(DeviceState).where(DeviceState.device_id == device_id))
    if result:
        return result.first()
    return None


async def get_device_state_by_device_id_and_parameter(session: AsyncSession, device_id: int, parameter: str) -> DeviceState | None:
    result = await session.scalars(select(DeviceState).where(
        DeviceState.device_id == device_id,
        DeviceState.parameter == parameter
    ))
    if result:
        return result.first()
    return None


async def get_or_create_device_state_by_device_id(session: AsyncSession, device_id: int, value: float, parameter: str | None = None, ) -> DeviceState:
    device_state = await get_device_state_by_device_id_and_parameter(
        session=session,
        device_id=device_id,
        parameter=parameter
    )
    if device_state is None:
        device_state = DeviceState(device_id=device_id, parameter=parameter, value=value)
        session.add(device_state)
        await session.commit()
        await session.refresh(device_state)
    return device_state


async def update_or_create_device_state_by_device_id(session: AsyncSession, device_id: int, value: float, parameter: str | None = None) -> DeviceState:
    device_state = await get_device_state_by_device_id_and_parameter(session, device_id, parameter)
    if device_state is None:
        device_state = DeviceState(device_id=device_id, parameter=parameter, value=value)
        session.add(device_state)
        await session.commit()
        await session.refresh(device_state)
    else:
        device_state.value = value
        device_state.last_updated = datetime.now()
        await session.commit()
        await session.refresh(device_state)
    return device_state

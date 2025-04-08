from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models import DeviceState, Device


async def get_device_state_by_device_id(session: AsyncSession, device_id: int) -> DeviceState | None:
    result = await session.scalars(select(DeviceState).where(DeviceState.device_id == device_id))
    if result:
        return result.first()
    return None


async def get_or_create_device_state_by_device_id(session: AsyncSession, device_id: int, value: str) -> DeviceState:
    device_state = await get_device_state_by_device_id(session, device_id)
    if device_state is None:
        device_state = DeviceState(device_id=device_id, value=value)
        session.add(device_state)
        await session.commit()
        await session.refresh(device_state)
    return device_state


async def update_or_create_device_state_by_device_id(session: AsyncSession, device_id: int, value: str) -> DeviceState:
    device_state = await get_device_state_by_device_id(session, device_id)
    if device_state is None:
        device_state = DeviceState(device_id=device_id, value=value)
        session.add(device_state)
        await session.commit()
        await session.refresh(device_state)
    else:
        device_state.value = value
        await session.commit()
        await session.refresh(device_state)
    return device_state

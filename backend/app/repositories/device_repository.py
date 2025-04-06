import asyncio
from sqlmodel import select

from app.core.db import AsyncSession
from app.models import Device


async def get_device_by_name_and_controller_id(session: AsyncSession, device_name: str, controller_id: int) -> Device | None:
    result = await session.exec(select(Device).where(Device.name == device_name, Device.controller_id == controller_id))
    return result.first()

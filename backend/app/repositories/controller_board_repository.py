import asyncio
from sqlmodel import select

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import async_engine
from app.models import ControllerBoard


async def get_controller_by_topic(session: AsyncSession, topic: str) -> ControllerBoard:
    result = await session.exec(select(ControllerBoard).where(ControllerBoard.topic == topic))
    return result.first()

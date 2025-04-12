import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlmodel import select, Session

from app.core.db import AsyncSession
# from sqlmodel.ext.asyncio.session import AsyncSession

# from app.core.db import async_engine
from app.models import ControllerBoard
from app.models.controller_board import logger


async def get_controller_by_topic(session: AsyncSession, topic: str) -> ControllerBoard:
    result = await session.scalars(select(ControllerBoard).where(ControllerBoard.topic == topic))
    return result.first()


async def create_or_update_controller_board(session: AsyncSession, topic: str, **kwargs):
    # Попробуем найти запись с данным topic
    statement = select(ControllerBoard).where(ControllerBoard.topic == topic)
    result = await session.scalars(statement)
    controller_board = result.first()

    # Если запись не найдена, создаем новую
    if not controller_board:
        controller_board = ControllerBoard(topic=topic, **kwargs)
        session.add(controller_board)
    else:
        # Если запись найдена, обновляем её
        for key, value in kwargs.items():
            if hasattr(controller_board, key):
                setattr(controller_board, key, value)
            else:
                logger.warning(f'Attribute {key} not found in ControllerBoard')
        controller_board.updated_at = datetime.now()
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise

    return controller_board

import pytest

from app.core.db import AsyncSession
from app.models import ControllerBoard
from app.repositories.controller_board_repository import create_or_update_controller_board

@pytest.mark.asyncio()
@pytest.mark.usefixtures('apply_migrations')
async def test_create_or_update_controller_board_create():
    async with AsyncSession() as session:
        controller = await create_or_update_controller_board(
            session=session,
            topic='test1/test2/test3',
            ip='127.0.0.1',
        )
    assert controller.id is not None


@pytest.mark.asyncio()
@pytest.mark.usefixtures('apply_migrations')
async def test_create_or_update_controller_board_update(created_controller_board):
    async with AsyncSession() as session:
        controller = await create_or_update_controller_board(
            session=session,
            topic=created_controller_board.topic,
            rabbitmq_user='test_user',
            period=60,
        )
    assert controller.id == created_controller_board.id
    async with AsyncSession() as session:
        controller = await session.get(ControllerBoard, created_controller_board.id)
    assert controller.rabbitmq_user == 'test_user'
    assert controller.period == 60



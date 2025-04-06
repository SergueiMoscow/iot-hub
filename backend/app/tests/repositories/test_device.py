import pytest
# from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import async_engine, AsyncSession
from app.repositories.device_repository import get_device_by_name_and_controller_id


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_get_device_by_name_and_controller_id(created_device):
    async with AsyncSession(async_engine) as session:
        device = get_device_by_name_and_controller_id(
            session=session,
            device_name=created_device.name,
            controller_id=created_device.controller_id
        )
    assert device is not None

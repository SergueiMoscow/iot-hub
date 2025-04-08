import pytest
from app.core.db import AsyncSession
from app.repositories.history_repository import get_history_by_hour_and_device_id


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_get_history_by_hour_and_device_id(created_device_history):
    async with AsyncSession() as session:
        device_state = await get_history_by_hour_and_device_id(
            session=session,
            device_id=created_device_history.device_id,
            hour=created_device_history.hour,
        )
    assert device_state is not None
    assert device_state.value == created_device_history.value

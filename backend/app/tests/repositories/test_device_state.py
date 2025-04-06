import pytest

from app.core.db import async_engine, AsyncSession, engine
from app.models import DeviceState
from app.repositories.device_state_repository import get_device_state_by_device_id, \
    get_or_create_device_state_by_device_id, update_or_create_device_state_by_device_id
from sqlmodel import Session, select


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_get_device_state_by_id(created_device_state):
    async with AsyncSession(async_engine) as session:
        device_state = await get_device_state_by_device_id(
            session=session,
            device_id=created_device_state.device_id,
        )
    assert device_state is not None
    assert device_state.value == created_device_state.value


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_get_device_state_by_id_not_found(created_device_state):
    async with AsyncSession(async_engine) as session:
        device_state = await get_device_state_by_device_id(
            session=session,
            device_id=created_device_state.device_id + 1,
        )
    assert device_state is None


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_get_or_create_device_state_by_device_id(created_device):
    value = 'on'
    async with AsyncSession(async_engine) as session:
        await get_or_create_device_state_by_device_id(
            session=session,
            device_id=created_device.id,
            value=value,
        )
        await session.commit()
    with Session(engine) as session:
        result = session.exec(select(DeviceState).where(DeviceState.device_id == created_device.id)).first()
        assert result is not None
        assert result.value == value

@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_update_or_create_device_state_by_device_id_create(created_device):
    value = 'on'
    async with AsyncSession(async_engine) as session:
        await update_or_create_device_state_by_device_id(
            session=session,
            device_id=created_device.id,
            value=value,
        )
        await session.commit()
    with Session(engine) as session:
        result = session.exec(select(DeviceState).where(DeviceState.device_id == created_device.id)).first()
        assert result is not None
        assert result.value == value


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_update_or_create_device_state_by_device_id_create(created_device_state):
    new_value = '20'
    async with AsyncSession(async_engine) as session:
        await update_or_create_device_state_by_device_id(
            session=session,
            device_id=created_device_state.device_id,
            value=new_value,
        )
        await session.commit()
    with Session(engine) as session:
        result = session.exec(select(DeviceState).where(DeviceState.device_id == created_device_state.device_id)).first()
        assert result is not None
        assert result.value == new_value

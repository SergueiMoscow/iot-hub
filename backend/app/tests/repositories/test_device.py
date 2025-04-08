import pytest
from app.core.db import AsyncSession
from app.models.device import DeviceCreate
from app.repositories.device_repository import get_device_by_name_and_controller_id, \
    get_or_create_device_by_name_and_controller_id


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_get_device_by_name_and_controller_id(created_device):
    async with AsyncSession() as session:
        device = await get_device_by_name_and_controller_id(
            session=session,
            device_name=created_device.name,
            controller_id=created_device.controller_id
        )
    assert device is not None
    assert device.id == created_device.id


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_create_new_device(created_controller_board):
    async with AsyncSession() as session:
        device_data = DeviceCreate(
            name="TestDevice",
            type="Relay",
            pin="D1",
            description="Test Description",
            device_key="device123",
            controller_id=created_controller_board.id,
        )

        # 1. Проверяем создание нового устройства
        device = await get_or_create_device_by_name_and_controller_id(
            session=session,
            device_data=device_data,
            controller_id=created_controller_board.id,
        )

        assert device.id is not None
        assert device.name == "TestDevice"

        # 2. Проверяем получение существующего устройства
        same_device = await get_or_create_device_by_name_and_controller_id(
            session=session,
            device_data=device_data,
            controller_id=created_controller_board.id,
        )

        assert same_device.id == device.id


@pytest.mark.asyncio
async def test_with_extra_name(created_controller_board):
    async with AsyncSession() as session:
        # 1. Создаем устройство с extra_name
        device = await get_or_create_device_by_name_and_controller_id(
            session=session,
            device_data={
                "name": "MultiSensor",
                "type": "DS18B20",
                "device_key": "sensor123",
                "extra_name": "sensor1",
            },
            controller_id=created_controller_board.id,
        )

        assert device.extra_name == "sensor1"

        # 2. Пытаемся получить то же устройство
        same_device = await get_or_create_device_by_name_and_controller_id(
            session=session,
            device_data={
                "name": "MultiSensor",
                "type": "DS18B20",
                "device_key": "sensor123",
                "extra_name": "sensor1",
            },
            controller_id=created_controller_board.id,
        )

        assert same_device.id == device.id


@pytest.mark.asyncio
async def test_invalid_device_data():
    async with AsyncSession() as session:
        with pytest.raises(ValueError):
            await get_or_create_device_by_name_and_controller_id(
                session=session,
                device_data={"type": "InvalidType"},
                controller_id=1
            )

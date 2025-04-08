import pytest
from app.core.db import AsyncSession
from app.services.process_startup_message import process_device


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_process_device_single(created_controller_board):
    async with AsyncSession() as session:
        # Тестируем обычное устройство (без датчиков)
        devices = await process_device(
            session=session,
            controller_id=created_controller_board.id,
            device_key='relay1',
            base_data={
                'name': 'TestRelay',
                'type': 'Relay',
                'pin': 'D1',
                'description': 'Test Relay Device',
                'device_key': 'relay1',
            }
        )

        assert len(devices) == 1
        device = devices[0]
        assert device.name == 'TestRelay'
        assert device.type == 'Relay'
        assert device.controller_id == created_controller_board.id


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_process_device_with_sensors(created_controller_board):
    async with AsyncSession() as session:
        # Тестируем устройство с датчиками (DS18B20)
        devices = await process_device(
            session=session,
            controller_id=created_controller_board.id,
            device_key='ds18b20_1',
            base_data={
                'name': 'TempSensors',
                'device_key': 'Device2',
                'type': 'DS18B20',
                'pin': 'D2',
                'description': 'Temperature Sensors',
            },
            sensors=[
                {'name': 'sensor1', 'description': 'Bedroom sensor'},
                {'name': 'sensor2', 'description': 'Kitchen sensor'}
            ]
        )

        assert len(devices) == 2
        assert all(device.type == 'DS18B20' for device in devices)
        assert {device.extra_name for device in devices} == {'sensor1', 'sensor2'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_process_device_dht(created_controller_board):
    async with AsyncSession() as session:
        # Тестируем DHT устройство
        devices = await process_device(
            session=session,
            controller_id=created_controller_board.id,
            device_key='dht22_1',
            base_data={
                'name': 'ClimateSensor',
                'device_key': 'Device3',
                'type': 'DHT',
                'pin': 'D3',
                'description': 'Climate Sensor'
            },
            sensors=['temperature', 'humidity']
        )

        assert len(devices) == 2
        assert {device.extra_name for device in devices} == {'temperature', 'humidity'}

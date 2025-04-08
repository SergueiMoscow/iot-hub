from copy import deepcopy
from typing import Optional
from sqlmodel import select
from app.core.db import AsyncSession
from app.models import Trigger, Device
from app.repositories.device_repository import get_or_create_device_by_name_and_controller_id


async def process_device(
        session: AsyncSession,
        controller_id: int,
        device_key: str,
        base_data: dict,
        sensors: Optional[list] = None
) -> list[Device]:
    """Обрабатывает устройство и его датчики (если есть)"""
    devices = []

    # Для обычных устройств
    if not sensors:
        device = await get_or_create_device_by_name_and_controller_id(
            session=session,
            device_data=base_data,
            controller_id=controller_id,
        )
        devices.append(device)
        return devices

    # Для устройств с датчиками (DS18B20/DHT)
    for sensor in sensors:
        sensor_data = {
            **base_data,
            "extra_name": sensor.get("name") if isinstance(sensor, dict) else sensor,
            "description": sensor.get("description") if isinstance(sensor, dict) else base_data.get("description")
        }
        device = await get_or_create_device_by_name_and_controller_id(
            session=session,
            device_data=sensor_data,
            controller_id=controller_id
        )
        devices.append(device)

    return devices


async def process_triggers(
        session: AsyncSession,
        device: Device,
        triggers_data: list[dict]
) -> None:
    """Создает или обновляет триггеры устройства"""
    for trigger_data in triggers_data:
        existing_trigger = await session.exec(
            select(Trigger).where(
                Trigger.device_id == device.id,
                Trigger.trigger_device == trigger_data['device'],
                Trigger.parameter == trigger_data['parameter'],
                Trigger.condition == trigger_data['condition'],
                Trigger.threshold == trigger_data['threshold']
            )
        ).first()

        if not existing_trigger:
            trigger = Trigger(
                **trigger_data,
                device_id=device.id,
                active=bool(trigger_data.get('active', True)),
            )
            session.add(trigger)

            await session.commit()


async def process_startup_message(
    session: AsyncSession,
    devices: dict,
    controller_id: int
) -> None:
    for device_key, device_data in devices.items():
        # Базовые данные устройства
        base_data = {
            "name": device_data["name"],
            "type": device_data["type"],
            "pin": device_data.get("pin"),
            "description": device_data.get("description"),
            "device_key": device_key,
            # "controller_id": controller_id,
        }

        # Обработка разных типов устройств
        match device_data["type"]:
            case "DS18B20":
                devices = await process_device(
                    session=session,
                    controller_id=controller_id,
                    device_key=device_key,
                    base_data=base_data,
                    sensors=device_data.get("sensors", [])
                )

            case "DHT":
                devices = await process_device(
                    session=session,
                    controller_id=controller_id,
                    device_key=device_key,
                    base_data=base_data,
                    sensors=["temperature", "humidity"]
                )

            case _:
                devices = await process_device(
                    session=session,
                    controller_id=controller_id,
                    device_key=device_key,
                    base_data=base_data
                )

        # Обработка триггеров для всех устройств
        for device in devices:
            if "triggers" in device_data:
                await process_triggers(
                    session=session,
                    device=device,
                    triggers_data=device_data["triggers"]
                )

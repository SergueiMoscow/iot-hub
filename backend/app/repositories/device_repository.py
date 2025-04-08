from typing import Optional

from sqlmodel import select

from app.core.db import AsyncSession
from app.models import Device
from app.models.device import DeviceCreate


async def get_device_by_name_and_controller_id(
        session: AsyncSession,
        device_name: str,
        controller_id: int,
        extra_name: Optional[str] = None
) -> Device | None:
    result = await session.scalars(
        select(Device).where(
            Device.name == device_name,
            Device.controller_id == controller_id,
            Device.extra_name == extra_name,
        )
    )
    return result.first()


async def get_or_create_device_by_name_and_controller_id(
        session: AsyncSession,
        controller_id: int,
        device_data: DeviceCreate | dict,
) -> Device:
    """Получает или создает устройство с проверкой уникальности по имени и controller_id."""
    if isinstance(device_data, dict):
        device_data = DeviceCreate(**device_data, controller_id=controller_id)

    # Ищем существующее устройство
    device = await get_device_by_name_and_controller_id(
        session=session,
        device_name=device_data.name,
        controller_id=controller_id,
        extra_name=device_data.extra_name,
    )

    if not device:
        # Создаем новое устройство
        device = Device(
            **device_data.model_dump(),
        )
        session.add(device)
        await session.commit()
        await session.refresh(device)

    return device

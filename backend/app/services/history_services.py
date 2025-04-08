from datetime import datetime, timezone
from typing import Optional, Union

from app.core.config import settings
from app.core.db import AsyncSession
from app.models import Device


def get_current_hour(
        time: Optional[Union[datetime, int, float]] = None
) -> datetime:
    """
    Возвращает время с обнулёнными минутами/секундами в settings.TIME_ZONE.
    - Если time=None или отличается от текущего на >24 часа → возвращает текущий час.
    - UNIX-время (int/float) считается UTC.
    - Наивный datetime (без временной зоны) считается локальным временем.
    """
    local_tz = settings.local_tz
    current_time = datetime.now(local_tz)

    # Если time=None, возвращаем текущий час
    if time is None:
        return current_time.replace(minute=0, second=0, microsecond=0)

    # Пытаемся преобразовать time в локальное время
    try:
        if isinstance(time, (int, float)):
            # UNIX-время → UTC → локальная зона
            utc_time = datetime.fromtimestamp(time, tz=timezone.utc)
            input_time = utc_time.astimezone(local_tz)
        elif time.tzinfo is None:
            # Наивный datetime → считаем локальным временем
            input_time = local_tz.localize(time)
        else:
            # datetime с временной зоной → конвертируем в локальную
            input_time = time.astimezone(local_tz)

        # Проверяем отклонение от текущего времени
        if abs((input_time - current_time).total_seconds()) <= 24 * 3600:
            return input_time.replace(minute=0, second=0, microsecond=0)

    except (ValueError, OSError):
        pass  # В случае ошибок игнорируем переданное время

    # Fallback: текущее время
    return current_time.replace(minute=0, second=0, microsecond=0)


async def save_to_history(
    session: AsyncSession,
    device: Device,
    data: dict,
):
    """
    Получаем Весь payload. Фильтруем его здесь.
    {"Bedroom":"on","Passage":"on","FloorSensors":{"Bedroom":26.5625,"Passage":26.5625},"RoomClimate":{"temperature":27.10000038,"humidity":37.79999924},"GasSensor":{"gas_raw":58,"gas_ppm":6.718621254},"time":1743968248}
    """
    # if device.type == 'Relay':
    #     value = data[device.name]
    # elif device.type == 'DS18B20':
    #     for sensor in data[device.name]:
    #     value = data[device.name]['temperature']
    # elif device.type == 'DHT22':
    #     value = data[device.name]['temperature']
    # else:
    #     return
    #
    # hour = get_current_hour()
    # await session.exec(
    #     insert(DeviceHistory).values(
    #         device_id=device.id,
    #         value=value,
    #         hour=hour,
    #     )
    # )
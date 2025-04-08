from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models import DeviceHistory


async def get_history_by_hour_and_device_id(
    session: AsyncSession,
    hour: datetime,
    device_id: int,
) -> DeviceHistory:
    if hour.minute == 0 and hour.second == 0:
        hour = hour.replace(minute=0, second=0, microsecond=0)
    result = await session.scalars(
        select(DeviceHistory).where(
            DeviceHistory.device_id == device_id,
            DeviceHistory.hour == hour,
        )
    )
    return result.first()

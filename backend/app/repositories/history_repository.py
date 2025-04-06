from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models import DeviceHistory


async def get_current_hour_history_by_device_id(session: AsyncSession, device_id: int) -> DeviceHistory:
    result = await session.exec(select(DeviceHistory).where(DeviceHistory.device_id == device_id))
    return result.first()

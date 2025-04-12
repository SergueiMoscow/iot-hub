from app.core.db import AsyncSession
from app.models.controller_file_request import ControllerFileRequest
from sqlalchemy import select, and_


async def create_controller_file_request(
    session: AsyncSession,
    controller_file_request: ControllerFileRequest
) -> ControllerFileRequest:

    session.add(controller_file_request)
    await session.commit()
    await session.refresh(controller_file_request)
    return controller_file_request

async def get_controller_file_request_by_topic_and_secret_key(
    session: AsyncSession,
    topic: str,
    secret_key: str
) -> ControllerFileRequest:
    result = await session.scalars(
        select(ControllerFileRequest).where(
            and_(
                ControllerFileRequest.topic == topic,
                ControllerFileRequest.secret_key == secret_key
            )
        )
    )
    return result.first()


async def delete_controller_file_request_by_topic_and_secret_key(
    session: AsyncSession,
    topic: str,
    secret_key: str
) -> None:
    controller_file_request = await get_controller_file_request_by_topic_and_secret_key(
        session,
        topic,
        secret_key,
    )
    if controller_file_request:
        await session.delete(controller_file_request)
        await session.commit()

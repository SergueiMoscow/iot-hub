from datetime import datetime

import pytest
import pytz

from app.core.db import AsyncSession
from app.models.controller_file_request import ControllerFileRequest
from app.repositories.controller_file_request_repository import create_controller_file_request


@pytest.mark.asyncio
@pytest.mark.usefixtures('apply_migrations')
async def test_create_new_controller_file_request():
    async with AsyncSession() as session:
        request = ControllerFileRequest(
            topic='test1/test2/test3',
            secret_key='test_secret_key',
            requested_at=datetime.now(),
            filename='test.json',
        )
        await create_controller_file_request(session=session, controller_file_request=request)

        assert request.id is not None
        assert request.topic == "test1/test2/test3"

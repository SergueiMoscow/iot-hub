from collections.abc import Generator

import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import ControllerBoard, Device, DeviceHistory
from app.models.device_state import DeviceStateCreate, DeviceState
from app.models.user import User
from app.models.item import Item
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers
from alembic import command
from sqlalchemy import text as sa_text
from alembic.config import Config


@pytest.fixture(scope="function")
def apply_migrations():
    backend_path = os.path.join(settings.PROJECT_PATH, "backend")
    assert "_test_" in str(settings.SQLALCHEMY_DATABASE_URI), "Попытка использовать не тестовую схему."
    alembic_ini = os.path.join(backend_path, "alembic.ini")

    # Создаём схему с использованием глобального engine
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT").execute(
            sa_text(f"CREATE SCHEMA IF NOT EXISTS {settings.POSTGRES_SCHEMA}")
        )

    # Настраиваем Alembic
    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))
    alembic_cfg.set_main_option("script_location", os.path.join(backend_path, "app", "alembic"))

    # Выполняем миграции
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

    yield command, alembic_cfg

    # Откатываем миграции
    command.downgrade(alembic_cfg, "base")

    # Удаляем схему
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT").execute(
            sa_text(f"DROP SCHEMA IF EXISTS {settings.POSTGRES_SCHEMA} CASCADE")
        )
    return


@pytest.fixture(scope="function", autouse=True)
def db(apply_migrations):
    from sqlmodel import Session
    with Session(engine) as session:
        init_db(session)
        yield session
    # statement = delete(Item)
    # session.execute(statement)
    # statement = delete(User)
    # session.execute(statement)
    # session.commit()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )

@pytest.fixture(scope="function")
def created_controller_board():
    controller_board = ControllerBoard(
        topic='test1/test2/test3',
        ip='111.11.11.11',
        rabbitmq_user='test1',
        period=20,
    )
    with Session(engine) as session:
        session.add(controller_board)
        session.commit()
        session.refresh(controller_board)
    return controller_board


@pytest.fixture(scope='function')
def created_device(created_controller_board):
    controller_board_id = created_controller_board.id
    device = Device(
        name='test_device',
        type='Relay',
        pin='D1',
        description='test description',
        device_key='device1',
        controller_id=controller_board_id
    )
    with Session(engine) as session:
        session.add(device)
        session.commit()
        session.refresh(device)
    return device


@pytest.fixture(scope='function')
def created_device_state(created_device):
    device_state = DeviceState(
        device_id=created_device.id,
        value='10',
    )
    with Session(engine) as session:
        session.add(device_state)
        session.commit()
        session.refresh(device_state)
    return device_state


@pytest.fixture(scope='function')
def create_device_history(created_device):
    def create(
        device_id=created_device.id,
        min_value='10',
        max_value='20',
        value='10',
        status='ok',
        hour=datetime.now().replace(minute=0, second=0, microsecond=0),
    ):

        device_history = DeviceHistory(
            device_id=device_id,
            min_value=min_value,
            max_value=max_value,
            value=value,
            status=status,
            hour=hour,
        )
        with Session(engine) as session:
            session.add(device_history)
            session.commit()
            session.refresh(device_history)
        return device_history
    return create

@pytest.fixture(scope='function')
def created_device_history(create_device_history):
    device_history = create_device_history(
        value='10',
    )
    with Session(engine) as session:
        session.add(device_history)
        session.commit()
        session.refresh(device_history)
    return device_history

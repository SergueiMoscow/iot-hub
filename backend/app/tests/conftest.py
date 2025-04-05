from collections.abc import Generator

import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models.user import User
from app.models.item import Item
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers
from alembic import command
from sqlalchemy import text as sa_text
from alembic.config import Config


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session", autouse=True)
def db(apply_migrations):
    from sqlmodel import Session
    with Session(engine) as session:
        init_db(session)
        yield session
    statement = delete(Item)
    session.execute(statement)
    statement = delete(User)
    session.execute(statement)
    session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )

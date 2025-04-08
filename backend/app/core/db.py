import contextlib

from sqlmodel import Session, create_engine, select, text
from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSessionSQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app import crud
from app.core.config import settings
from app.models.user import User, UserCreate

# Синхронный движок
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

# Асинхронный движок
# def get_async_engine():
#     uri = str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql+psycopg", "postgresql+asyncpg")
#     if 'options' in uri:
#         uri = uri.split('?')[0]
#     async_engine = create_async_engine(
#         uri,
#         echo=True,
#         future=True
#     )
#     return async_engine

# async_engine = get_async_engine()

# class AsyncSession(AsyncSessionSQLModel):
#     async def __aenter__(self):
#         await super().__aenter__()
#         await self.exec(text(f'SET search_path TO {settings.POSTGRES_SCHEMA}'))
#         await self.commit()
#         return self


class DatabaseConnector:
    @staticmethod
    def get_engine():
        """Синхронный движок для основного кода"""
        return create_engine(
            str(settings.SQLALCHEMY_DATABASE_URI),
            pool_pre_ping=True
        )

    @staticmethod
    def get_async_engine():
        """Асинхронный движок для основного кода"""
        uri = str(settings.SQLALCHEMY_DATABASE_URI)
        if 'options' in uri:
            uri = uri.split('?')[0]
        return create_async_engine(
            uri.replace(
                "postgresql+psycopg",
                "postgresql+asyncpg"
            ),
            pool_pre_ping=True,
            echo=settings.DEBUG
        )

    @classmethod
    @contextlib.contextmanager
    def get_sync_session(cls):
        """Синхронная сессия (для CLI, миграций и т.д.)"""
        engine = cls.get_engine()
        Session = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        with Session() as session:
            try:
                yield session
            finally:
                session.close()

    @classmethod
    @contextlib.asynccontextmanager
    async def get_async_session(cls):
        """Основная асинхронная сессия для приложения"""
        async_engine = cls.get_async_engine()
        AsyncSession = async_sessionmaker(
            bind=async_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        async with AsyncSession() as session:
            try:
                # Устанавливаем схему из настроек
                await session.execute(text(f"SET search_path TO {settings.POSTGRES_SCHEMA}"))
                yield session
            finally:
                await session.close()

# Глобальные фабрики сессий
SyncSession = DatabaseConnector.get_sync_session
AsyncSession = DatabaseConnector.get_async_session

def init_db(session: Session) -> None:
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

async def async_init_db(session: AsyncSession) -> None:
    async with session.begin():
        result = await session.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        )
        user = result.first()
        if not user:
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
            )
            user = await crud.async_create_user(session=session, user_create=user_in)

if __name__ == "__main__":
    init_db(Session(engine))

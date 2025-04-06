from sqlmodel import Session, create_engine, select, text
from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSessionSQLModel
from sqlalchemy.ext.asyncio import create_async_engine

from app import crud
from app.core.config import settings
from app.models.user import User, UserCreate

# Синхронный движок
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

# Асинхронный движок
print("URI:" + str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql+psycopg", "postgresql+asyncpg"))
def get_async_engine():
    uri = str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql+psycopg", "postgresql+asyncpg")
    if 'options' in uri:
        uri = uri.split('?')[0]
    async_engine = create_async_engine(
        uri,
        echo=True,
        future=True
    )
    return async_engine

async_engine = get_async_engine()

class AsyncSession(AsyncSessionSQLModel):
    async def __aenter__(self):
        await super().__aenter__()
        await self.exec(text(f'SET search_path TO {settings.POSTGRES_SCHEMA}'))
        await self.commit()
        return self


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

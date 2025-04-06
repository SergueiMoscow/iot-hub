from sqlmodel import Session, create_engine, select, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession as AsyncSessionSQLAlchemy, create_async_engine, async_sessionmaker
import sys
from app import crud
from app.core.config import settings
from app.models.user import User, UserCreate

# Синхронный движок
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

# Асинхронный движок
async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql+psycopg", "postgresql+asyncpg"),
    echo=True,
    future=True
)

# Создаем фабрику сессий
AsyncSession = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSessionSQLAlchemy
)

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

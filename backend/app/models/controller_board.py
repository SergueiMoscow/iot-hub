import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime, func, Session
from app.models.user import User
from sqlalchemy.exc import IntegrityError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ControllerBoardBase(SQLModel):
    topic: str = Field(max_length=255, unique=True)
    ip: str = Field(max_length=15, nullable=True)
    rabbitmq_user: str = Field(max_length=50, nullable=True)
    last_seen: datetime = Field(default_factory=datetime.now, nullable=False)
    period: int = Field(default=60, nullable=False)
    description: str = Field(max_length=255, nullable=True, default='')
    access_key: str = Field(max_length=32, nullable=False, default='')
    created_at: datetime =(
        Field(
            sa_column=Column(
                DateTime(timezone=True),
                server_default=func.now(),
                nullable=False
            )
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            server_onupdate=func.now(),
            onupdate=func.now(),
            nullable=False
        )
    )

class ControllerBoard(ControllerBoardBase, table=True):
    id: int = Field(primary_key=True, index=True)
    # owner_id: uuid.UUID = Field(
    #     foreign_key="user.id", nullable=False, ondelete="CASCADE"
    # )
    # owner: User | None = Relationship(back_populates="boards")

class ControllerBoardPublic(ControllerBoardBase):
    id: int


# @event.listens_for(Session, 'before_commit')
# def receive_before_commit(session):
#     for instance in session.dirty:
#         if isinstance(instance, ControllerBoard):
#             instance.updated_at = datetime.now()


async def create_or_update_controller_board(session: Session, topic: str, **kwargs):
    # Попробуем найти запись с данным topic
    statement = select(ControllerBoard).where(ControllerBoard.topic == topic)
    result = session.exec(statement)
    controller_board_row = result.first()

    # Если запись не найдена, создаем новую
    if not controller_board_row:
        controller_board = ControllerBoard(topic=topic, **kwargs)
        session.add(controller_board)
    else:
        # Если запись найдена, обновляем её
        controller_board = controller_board_row[0]

        # Если запись найдена, обновляем её
        for key, value in kwargs.items():
            if hasattr(controller_board, key):
                setattr(controller_board, key, value)
            else:
                logger.warning(f'Attribute {key} not found in ControllerBoard')
        controller_board.updated_at = datetime.now()
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise

    return controller_board

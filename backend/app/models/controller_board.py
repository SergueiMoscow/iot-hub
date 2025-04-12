import logging
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime, func
from typing import Optional, List

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

class ControllerBoard(ControllerBoardBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
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
    devices: List["Device"] = Relationship(back_populates="controller")


class ControllerBoardPublic(ControllerBoardBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ControllerBoardsPublic(SQLModel):
    data: list[ControllerBoardPublic]
    count: int


# @event.listens_for(Session, 'before_commit')
# def receive_before_commit(session):
#     for instance in session.dirty:
#         if isinstance(instance, ControllerBoard):
#             instance.updated_at = datetime.now()



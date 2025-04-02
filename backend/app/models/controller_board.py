import uuid
from datetime import datetime

from sqlalchemy import event
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime, func, Session
from app.models.user import User


class ControllerBoardBase(SQLModel):
    topic: str = Field(max_length=255, unique=True)
    ip: str = Field(max_length=15)
    rabbitmq_user: str = Field(max_length=50)
    last_seen: datetime = Field(default_factory=datetime.now, nullable=False)
    period: int = Field(default=60, nullable=False)
    description: str = Field(max_length=255, nullable=True)
    access_key: str = Field(max_length=32, nullable=False)
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
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), onupdate=func.now(), nullable=False)
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

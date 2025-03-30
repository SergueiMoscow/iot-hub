from datetime import datetime
from sqlmodel import Field, SQLModel

class BoardBase(SQLModel):
    topic: str = Field(max_length=255, unique=True)
    ip: str = Field(max_length=15)
    rabbitmq_user: str = Field(max_length=50)
    last_seen: datetime = Field(default_factory=datetime.now, nullable=False)
    period: int = Field(default=60, nullable=False)
    description: str = Field(max_length=255, nullable=True)
    # is_online: bool = Field(default=False)
    access_key: str = Field(max_length=32, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


class Board(BoardBase, table=True):
    id: int = Field(primary_key=True, index=True)

class BoardPublic(BoardBase):
    id: int

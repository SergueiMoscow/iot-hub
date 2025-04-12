from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
import pytz

class ControllerFileRequestBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic: str = Field(max_length=255, nullable=False)
    secret_key: str = Field(max_length=64, nullable=False)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(pytz.utc), nullable=False)
    filename: str = Field(max_length=255, nullable=False)

class ControllerFileRequest(ControllerFileRequestBase, table=True):
    pass


class ControllerFileRequestCreate(ControllerFileRequestBase):
    pass


class ControllerFileRequestPublic(ControllerFileRequestBase):
    pass

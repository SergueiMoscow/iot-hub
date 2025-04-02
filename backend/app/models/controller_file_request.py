from datetime import datetime
from sqlmodel import Field, SQLModel
import pytz

class ControllerFileRequestBase(SQLModel):
    topic: str = Field(max_length=255, nullable=False)
    secret_key: str = Field(max_length=64, nullable=False)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(pytz.utc), nullable=False)
    filename: str = Field(max_length=255, nullable=False)

class ControllerFileRequest(ControllerFileRequestBase, table=True):
    id: int = Field(primary_key=True, index=True)

class ControllerFileRequestCreate(ControllerFileRequestBase):
    pass

class ControllerFileRequestPublic(ControllerFileRequestBase):
    id: int

from datetime import datetime
from sqlmodel import Field, SQLModel
import pytz

class DeviceFileRequestBase(SQLModel):
    topic: str = Field(max_length=255, nullable=False)
    secret_key: str = Field(max_length=64, nullable=False)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(pytz.utc), nullable=False)
    filename: str = Field(max_length=255, nullable=False)

class DeviceFileRequest(DeviceFileRequestBase, table=True):
    id: int = Field(primary_key=True, index=True)

class DeviceFileRequestCreate(DeviceFileRequestBase):
    pass

class DeviceFileRequestPublic(DeviceFileRequestBase):
    id: int

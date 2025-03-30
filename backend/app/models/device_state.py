# backend/app/models/device_state.py
from datetime import datetime
from sqlmodel import Field, SQLModel

class DeviceStateBase(SQLModel):
    board_id: int = Field(foreign_key='board.id')
    type: str = Field(max_length=50)  # 'sensor' или 'relay'
    name: str = Field(max_length=50)
    value: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)

class DeviceState(DeviceStateBase, table=True):
    id: int = Field(primary_key=True, index=True)

class DeviceStatePublic(DeviceStateBase):
    id: int
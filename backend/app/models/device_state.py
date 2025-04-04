from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from pydantic import validator

# from app.models.device import Device


class DeviceStateBase(SQLModel):
    value: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class DeviceStateCreate(DeviceStateBase):
    device_id: int

class DeviceStateUpdate(SQLModel):
    value: Optional[str] = None
    last_updated: Optional[datetime] = None

class DeviceState(DeviceStateBase, table=True):
    device_id: int = Field(foreign_key="device.id", primary_key=True)
    device: Optional["Device"] = Relationship(back_populates="states")

class DeviceStatePublic(SQLModel):
    topic: str  # из ControllerBoard
    controller_description: str  # из ControllerBoard
    device_name: str
    device_type: str
    device_description: Optional[str]
    value: str
    last_updated: datetime

    @classmethod
    def from_orm(cls, db_state: DeviceState):
        return cls(
            topic=db_state.device.controller.topic,
            controller_description=db_state.device.controller.description,
            device_name=db_state.device.name,
            device_type=db_state.device.type,
            device_description=db_state.device.description,
            value=db_state.value,
            last_updated=db_state.last_updated
        )

class DeviceStatesPublic(SQLModel):
    data: list[DeviceStatePublic]
    count: int

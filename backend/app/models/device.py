from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator
from app.models.device_state import DeviceState
from app.models.trigger import Trigger
from typing import Optional, List


class DeviceBase(SQLModel):
    name: str = Field(max_length=255)
    type: str = Field(max_length=50)
    pin: Optional[str] = Field(max_length=10, default=None)
    description: Optional[str] = Field(default=None)
    device_key: str

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed_types = {'Relay', 'Buzzer', 'RFID', 'DS18B20', 'DHT', 'MQ'}
        if v not in allowed_types:
            raise ValueError(f"Device type must be one of {allowed_types}")
        return v

class DeviceCreate(DeviceBase):
    controller_id: int


class DeviceUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=255)
    type: Optional[str] = Field(default=None, max_length=50)
    pin: Optional[str] = Field(default=None, max_length=10)
    description: Optional[str] = Field(default=None)


class Device(DeviceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    controller_id: int = Field(foreign_key="controllerboard.id")

    states: Optional["DeviceState"] = Relationship(back_populates="device")
    triggers: List["Trigger"] = Relationship(back_populates="device")
    controller: Optional["ControllerBoard"] = Relationship(back_populates="devices")
    history: List["DeviceHistory"] = Relationship(back_populates="device")


class DevicePublic(DeviceBase):
    id: int
    controller_id: int


class DevicesPublic(SQLModel):
    data: list[DevicePublic]
    count: int

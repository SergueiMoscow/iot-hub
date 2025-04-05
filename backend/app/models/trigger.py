from sqlmodel import SQLModel, Field, Relationship
from typing import Optional


class Trigger(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="device.id")
    trigger_device: str
    parameter: str
    condition: str
    threshold: float
    action: str
    active: bool = Field(default=True)

    device: Optional['Device'] = Relationship(back_populates="triggers")

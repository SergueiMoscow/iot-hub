from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class DeviceHistoryBase(SQLModel):
    device_id: int = Field(foreign_key="device.id", primary_key=True)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    value: Optional[str] = None
    status: Optional[str] = None
    hour: datetime = Field(default_factory=datetime.now, nullable=False)
    last_updated: datetime = Field(default_factory=datetime.now, nullable=False)

class DeviceHistory(DeviceHistoryBase, table=True):
    device: Optional["Device"] = Relationship(back_populates="history")

class DeviceHistoryPublic(DeviceHistoryBase):
    device_name: str
    device_type: str

    @classmethod
    def from_db_history(cls, db_history: DeviceHistory):
        return cls(
            device_id=db_history.device_id,
            device_name=db_history.device.name,
            device_type=db_history.device.type,
            min_value=db_history.min_value,
            max_value=db_history.max_value,
            relay_on_count=db_history.relay_on_count,
            relay_off_count=db_history.relay_off_count,
            rfid_success_count=db_history.rfid_success_count,
            rfid_fail_count=db_history.rfid_fail_count,
            last_updated=db_history.last_updated
        )

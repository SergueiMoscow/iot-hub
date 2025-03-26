from datetime import datetime
from sqlmodel import Field, SQLModel


# Базовые свойства устройства
class DeviceDataBase(SQLModel):
    object: str = Field(max_length=255, nullable=False)
    room: str = Field(max_length=255, nullable=False)
    device: str = Field(max_length=255, nullable=False)
    state: str = Field(max_length=255, nullable=False)
    module: str = Field(max_length=255, nullable=False)
    value: str = Field(max_length=255, nullable=False)
    timestamp: datetime = Field(default_factory=datetime.now, nullable=False)


# Модель для создания через API
class DeviceDataCreate(DeviceDataBase):
    pass  # Все поля уже в DeviceDataBase, дополнительных нет


# Модель для обновления через API (все поля опциональны)
class DeviceDataUpdate(SQLModel):
    object: str | None = Field(default=None, max_length=255)
    room: str | None = Field(default=None, max_length=255)
    device: str | None = Field(default=None, max_length=255)
    state: str | None = Field(default=None, max_length=255)
    module: str | None = Field(default=None, max_length=255)
    value: str | None = Field(default=None, max_length=255)
    timestamp: datetime | None = Field(default=None)


# Модель базы данных
class DeviceData(DeviceDataBase, table=True):
    id: int = Field(primary_key=True, index=True)  # BigInteger как int с autoincrement


# Модель для ответа API
class DeviceDataPublic(DeviceDataBase):
    id: int  # Включаем id в ответ


# Модель для списка устройств
class DeviceDataList(SQLModel):
    data: list[DeviceDataPublic]
    count: int

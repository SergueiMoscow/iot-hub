import json
import logging
import pytz
from datetime import datetime

from sqlmodel import Session, select, and_

from app.core.db import engine
from app.models import DeviceState, ControllerBoard
from app.models.device import Device, DeviceCreate
from app.models.device_history import DeviceHistory
from app.models.trigger import Trigger


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def process_startup_message(session: Session, devices: dict, controller_id: int):
    for device_key, device_data in devices.items():
        # Проверяем наличие устройства в базе
        existing_device = session.exec(select(Device).filter_by(
            controller_id=controller_id,
            pin=device_data.get('pin'),
            name=device_data['name'],
            type=device_data['type'],
        )).first()

        if not existing_device:
            # Создаем новое устройство
            device_create = DeviceCreate(
                name=device_data['name'],
                type=device_data['type'],
                pin=device_data.get('pin'),
                description=device_data.get('description'),
                controller_id=controller_id,
                device_key=device_key
            )
            existing_device = Device.model_validate(device_create)
            session.add(existing_device)

        session.commit()
        session.refresh(existing_device)

        # Обрабатываем датчики для DS18B20
        if device_data['type'] == 'DS18B20':
            for sensor in device_data.get('sensors', []):
                sensor_name = f"{device_data['name']}_{sensor['name']}"
                sensor_description = sensor.get('description')

                # Проверяем наличие датчика в базе
                existing_sensor = session.exec(select(Device).filter_by(
                    controller_id=controller_id,
                    pin=device_data.get('pin'),
                    name=sensor_name
                )).first()

                if existing_sensor:
                    # Обновляем существующий датчик
                    existing_sensor.description = sensor_description
                    session.add(existing_sensor)
                else:
                    # Создаем новый датчик
                    sensor_create = DeviceCreate(
                        name=sensor_name,
                        type='DS18B20',
                        pin=device_data.get('pin'),
                        description=sensor_description,
                        controller_id=controller_id,
                        device_key=device_key
                    )
                    sensor_device = Device.model_validate(sensor_create)
                    session.add(sensor_device)


        session.commit()

        # Обрабатываем триггеры для устройства
        for trigger_data in device_data.get('triggers', []):
            # Проверяем наличие триггера
            statement = select(Trigger).where(
                Trigger.device_id == existing_device.id,
                Trigger.trigger_device == trigger_data['device'],
                Trigger.parameter == trigger_data['parameter'],
                Trigger.condition == trigger_data['condition'],
                Trigger.threshold == trigger_data['threshold'],
            )
            existing_trigger = session.exec(statement).first()

            if not existing_trigger:
                # Создаем новый триггер
                trigger = Trigger(
                    device_id=existing_device.id,
                    trigger_device=trigger_data['device'],
                    parameter=trigger_data['parameter'],
                    condition=trigger_data['condition'],
                    threshold=trigger_data['threshold'],
                    action=trigger_data.get('action', ''),
                    active=bool(trigger_data.get('active', True)),
                )
                session.add(trigger)

def process_state_message(payload: dict, topic: str):
    with Session(engine) as session:
        controller = session.exec(
            select(ControllerBoard).filter_by(topic=topic)
        ).first()
        if not controller:
            logger.error(f"Controller with topic {topic} not found")
            return

        for device_name, state in payload.items():
            device = session.exec(select(Device).filter_by(name=device_name, controller_id=controller.id)).first()
            if not device:
                logger.error(f"Device {device_name} not found for controller {controller.id}")
                continue

            # Update DeviceState
            device_state = DeviceState(device_id=device.id, value=json.dumps(state))
            session.add(device_state)

            # Update DeviceHistory
            device_history = session.exec(select(DeviceHistory).filter_by(device_id=device.id)).first()
            if not device_history:
                device_history = DeviceHistory(device_id=device.id)
                session.add(device_history)

            if device.type == 'Sensor':
                device_history.min_value = min(device_history.min_value or float('inf'), state)
                device_history.max_value = max(device_history.max_value or float('-inf'), state)
            elif device.type == 'Relay':
                if state == 'on':
                    device_history.relay_on_count += 1
                elif state == 'off':
                    device_history.relay_off_count += 1
            elif device.type == 'RFID':
                if state == 'success':
                    device_history.rfid_success_count += 1
                elif state == 'fail':
                    device_history.rfid_fail_count += 1

            device_history.last_updated = datetime.now(pytz.utc)
            session.commit()

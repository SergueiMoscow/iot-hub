from .controller_board import ControllerBoard
from .device import Device
from .device_state import DeviceState
from .trigger import Trigger

ControllerBoard.model_rebuild()
Device.model_rebuild()
DeviceState.model_rebuild()
Trigger.model_rebuild()
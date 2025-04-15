from fastapi import Depends, Request


def get_mqtt_manager(request: Request):
    """
    Зависимость для получения MQTTClientManager из app.state.mqtt_manager.
    Использует Request для доступа к app.state, чтобы избежать циклического импорта.
    """
    return request.app.state.mqtt_manager

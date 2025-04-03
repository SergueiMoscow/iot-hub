import json

def get_active_mqtt_config(file_path: str) -> dict | None:
    with open(file_path, 'r') as file:
        data = json.load(file)

    for key, value in data.items():
        if value.get("Active") == 1:
            return value

    return None

import requests
from typing import Dict

from app.core.config import settings

def get_rabbitmq_connections() -> Dict:
    """
    Получает список текущих соединений RabbitMQ и возвращает их в виде словаря.

    Returns:
        Dict: Словарь с информацией о соединениях
    """
    try:
        # Формируем URL для API RabbitMQ
        api_url = f"http://{settings.RABBITMQ_HOST}:{settings.RABBITMQ_API_PORT}/api/connections"

        # Учетные данные для авторизации
        auth = (settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)

        # Делаем HTTP запрос к API RabbitMQ
        response = requests.get(api_url, auth=auth, timeout=10)

        # Проверяем успешность запроса
        response.raise_for_status()

        # Парсим JSON ответ
        connections_data = response.json()

        # Формируем словарь с нужной информацией
        connections_dict = {}
        for conn in connections_data:
            conn_id = conn.get('name', 'unknown')
            connections_dict[conn_id] = {
                'client': conn.get('client_properties', {}).get('product', 'unknown'),
                'host': conn.get('host', 'unknown'),
                'port': conn.get('port', 'unknown'),
                'state': conn.get('state', 'unknown'),
                'channels': conn.get('channels', 0),
                'connected_at': conn.get('connected_at', 'unknown')
            }

        return connections_dict

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при подключении к RabbitMQ API: {str(e)}")
        return {}
    except Exception as e:
        print(f"Непредвиденная ошибка: {str(e)}")
        return {}


# Пример использования:
if __name__ == "__main__":
    try:
        connections = get_rabbitmq_connections()
        print("Текущие соединения:")
        for conn_id, details in connections.items():
            print(f"Соединение {conn_id}:")
            for key, value in details.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"Ошибка при выполнении: {e}")
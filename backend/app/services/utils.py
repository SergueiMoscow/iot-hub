import json

def is_json(myjson):
  try:
    json.loads(myjson)
    if not isinstance(myjson, str) or not '"' in myjson:
        return False
  except ValueError as e:
    return False
  except Exception as e:
    return False
  return True

def get_root_topic(topic: str) -> str:
  """
      Оставляет только первые 3 элемента в строке, разделённой косыми чертами.

      'flat/room/controller'
      """
  parts = [part for part in topic.split('/') if part][:3]  # Убираем пустые части и берём первые 3
  return '/'.join(parts)

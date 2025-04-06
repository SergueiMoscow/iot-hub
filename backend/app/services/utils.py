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

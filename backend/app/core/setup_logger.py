import logging
from functools import lru_cache


@lru_cache(maxsize=None)
def setup_logger(name: str) -> logging.Logger:
    """
    Настраивает и возвращает логгер с указанным именем.
    Использует кэширование, чтобы избежать дублирования обработчиков.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Создаем обработчик для вывода в консоль
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # Настраиваем формат сообщений
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Добавляем обработчик к логгеру
    logger.addHandler(handler)

    return logger

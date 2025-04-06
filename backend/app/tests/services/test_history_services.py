import pytest
from datetime import datetime, timezone
import pytz

from app.core.config import settings
from app.services.history_services import get_current_hour

TEST_UNIX_TIME = 1743968248  # 2025-04-06 19:37:28 UTC → 22:37:28 MSK (UTC+3)
EXPECTED_TRUNCATED = datetime(2025, 4, 6, 22, 0, 0)  # Ожидаемый результат после обнуления


@pytest.mark.parametrize("input_time, expected_hour", [
    # Текущее время (None)
    (None, datetime.now(pytz.timezone('Europe/Moscow')).replace(minute=0, second=0, microsecond=0)),

    # Наивный datetime (без временной зоны)
    (
            datetime(2025, 4, 6, 22, 37, 28),
            datetime(2025, 4, 6, 22, 0, 0)
    ),

    # datetime с временной зоной (UTC)
    (
            datetime(2025, 4, 6, 19, 37, 28, tzinfo=timezone.utc),
            datetime(2025, 4, 6, 22, 0, 0)  # UTC+3 → Moscow Time
    ),

    # UNIX-время (int)
    (
            TEST_UNIX_TIME,
            EXPECTED_TRUNCATED
    ),

    # UNIX-время (float)
    (
            float(TEST_UNIX_TIME),
            EXPECTED_TRUNCATED
    ),
])
def test_get_current_hour(input_time, expected_hour):
    result = get_current_hour(input_time)
    expected = expected_hour

    # Для None сравниваем приблизительно (текущее время может немного отличаться)
    assert result.replace(tzinfo=None) == expected.replace(tzinfo=None)
    assert result.minute == 0
    assert result.second == 0
    assert result.microsecond == 0

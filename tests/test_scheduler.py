from datetime import datetime
from zoneinfo import ZoneInfo

from src.scheduler import (
    is_due_calendar_day,
    is_due_interval_after_success,
    is_task_due,
    stable_delay_minutes,
)


def test_calendar_day_is_due_after_local_midnight_and_earliest_time():
    now = datetime(2026, 6, 2, 0, 20, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert is_due_calendar_day(
        now=now,
        last_success_date="2026-06-01",
        timezone="Asia/Shanghai",
        earliest_time="00:05",
        random_delay_minutes=[0, 0],
        seed="main:midnight_bot",
    )


def test_calendar_day_is_not_due_twice_on_same_local_date():
    now = datetime(2026, 6, 2, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert not is_due_calendar_day(
        now=now,
        last_success_date="2026-06-02",
        timezone="Asia/Shanghai",
        earliest_time="00:05",
        random_delay_minutes=[0, 0],
        seed="main:midnight_bot",
    )


def test_interval_after_success_waits_until_full_interval_passes():
    now = datetime(2026, 6, 2, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert not is_due_interval_after_success(
        now=now,
        last_success_at="2026-06-01T09:30:00+08:00",
        min_interval_hours=24,
        random_delay_minutes=[0, 0],
        seed="main:interval_bot",
    )


def test_interval_after_success_is_due_after_interval_passes():
    now = datetime(2026, 6, 2, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert is_due_interval_after_success(
        now=now,
        last_success_at="2026-06-01T09:30:00+08:00",
        min_interval_hours=24,
        random_delay_minutes=[0, 0],
        seed="main:interval_bot",
    )


def test_stable_delay_is_repeatable_for_same_seed():
    first = stable_delay_minutes("main:bot:2026-06-02", [5, 45])
    second = stable_delay_minutes("main:bot:2026-06-02", [5, 45])

    assert first == second
    assert 5 <= first <= 45


def test_is_task_due_dispatches_by_schedule_mode():
    now = datetime(2026, 6, 2, 0, 20, tzinfo=ZoneInfo("Asia/Shanghai"))
    task = {
        "name": "midnight_bot",
        "schedule": {
            "mode": "calendar_day",
            "timezone": "Asia/Shanghai",
            "earliest_time": "00:05",
            "random_delay_minutes": [0, 0],
        },
    }

    assert is_task_due(now, "main", task, {"last_success_date": "2026-06-01"})

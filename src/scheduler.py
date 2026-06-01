from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from hashlib import sha256
from zoneinfo import ZoneInfo

from src.state_store import state_key


def stable_delay_minutes(seed: str, window: list[int] | tuple[int, int]) -> int:
    low, high = int(window[0]), int(window[1])
    if high < low:
        raise ValueError("random_delay_minutes must be [low, high] with high >= low")
    if high == low:
        return low
    digest = sha256(seed.encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big")
    return low + (value % (high - low + 1))


def _parse_hhmm(value: str) -> time:
    hour_text, minute_text = value.split(":", 1)
    return time(int(hour_text), int(minute_text))


def _parse_iso_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ZoneInfo("UTC"))
    return parsed


def _record_next_eligible_at(record: dict | None) -> datetime | None:
    if not record:
        return None
    value = record.get("next_eligible_at")
    if not value:
        return None
    return _parse_iso_datetime(value)


def is_due_calendar_day(
    now: datetime,
    last_success_date: str | None,
    timezone: str,
    earliest_time: str,
    random_delay_minutes: list[int] | tuple[int, int],
    seed: str,
) -> bool:
    local_now = now.astimezone(ZoneInfo(timezone))
    today = local_now.date().isoformat()
    if last_success_date == today:
        return False
    if last_success_date and last_success_date > today:
        return False
    earliest_local = datetime.combine(local_now.date(), _parse_hhmm(earliest_time), tzinfo=ZoneInfo(timezone))
    due_at = earliest_local + timedelta(minutes=stable_delay_minutes(f"{seed}:{today}", random_delay_minutes))
    return local_now >= due_at


def is_due_interval_after_success(
    now: datetime,
    last_success_at: str | None,
    min_interval_hours: int,
    random_delay_minutes: list[int] | tuple[int, int],
    seed: str,
) -> bool:
    if not last_success_at:
        return True
    last_success = _parse_iso_datetime(last_success_at)
    due_at = last_success + timedelta(
        hours=int(min_interval_hours),
        minutes=stable_delay_minutes(f"{seed}:{last_success_at}", random_delay_minutes),
    )
    return now >= due_at


def is_task_due(now: datetime, account_name: str, task: dict, record: dict | None) -> bool:
    schedule = task.get("schedule", {})
    mode = schedule.get("mode")
    record = record or {}
    seed = state_key(account_name, task["name"])
    next_eligible_at = _record_next_eligible_at(record)
    if next_eligible_at and now < next_eligible_at:
        return False
    if mode == "calendar_day":
        return is_due_calendar_day(
            now=now,
            last_success_date=record.get("last_success_date"),
            timezone=schedule.get("timezone", "Asia/Shanghai"),
            earliest_time=schedule.get("earliest_time", "00:05"),
            random_delay_minutes=schedule.get("random_delay_minutes", [0, 0]),
            seed=seed,
        )
    if mode == "interval_after_success":
        return is_due_interval_after_success(
            now=now,
            last_success_at=record.get("last_success_at"),
            min_interval_hours=int(schedule.get("min_interval_hours", 24)),
            random_delay_minutes=schedule.get("random_delay_minutes", [0, 0]),
            seed=seed,
        )
    raise ValueError(f"Unsupported schedule mode: {mode}")

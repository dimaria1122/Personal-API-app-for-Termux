from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

ResponseStatus = Literal["success", "deferred", "unknown"]

_SUCCESS_PATTERNS = (
    re.compile(r"今日已签到"),
    re.compile(r"签到成功"),
    re.compile(r"已经签到"),
    re.compile(r"已签到"),
)

_DEFERRED_PATTERN = re.compile(
    r"(?:请等待|请稍后)\s*"
    r"(?:(?P<hours>\d+)\s*小时\s*)?"
    r"(?:(?P<minutes>\d+)\s*分钟)?"
    r"(?:后再来签到|后再来|后再试|后再签到)"
)


@dataclass(slots=True)
class ResponseParseResult:
    status: ResponseStatus
    next_eligible_at: datetime | None = None


def _parse_wait_delta(response_text: str) -> timedelta | None:
    match = _DEFERRED_PATTERN.search(response_text)
    if not match:
        return None
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    if hours == 0 and minutes == 0:
        return None
    return timedelta(hours=hours, minutes=minutes)


def parse_bot_response(response_text: str, now: datetime | None = None) -> ResponseParseResult:
    text = (response_text or "").strip()
    if not text:
        return ResponseParseResult(status="unknown")

    for pattern in _SUCCESS_PATTERNS:
        if pattern.search(text):
            return ResponseParseResult(status="success")

    wait_delta = _parse_wait_delta(text)
    if wait_delta is not None:
        current = now or datetime.now().astimezone()
        return ResponseParseResult(status="deferred", next_eligible_at=current + wait_delta)

    return ResponseParseResult(status="unknown")


evaluate_bot_response = parse_bot_response

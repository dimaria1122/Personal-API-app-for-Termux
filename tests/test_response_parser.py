from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

from src.response_parser import parse_bot_response


def test_parse_deferred_response_with_hours_and_minutes():
    now = datetime(2026, 6, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    result = parse_bot_response("⏳ 签到太频繁啦！请等待 4 小时 32 分钟后再来签到。", now=now)

    assert result.status == "deferred"
    assert result.next_eligible_at == now + timedelta(hours=4, minutes=32)


def test_parse_deferred_response_with_minutes_only():
    now = datetime(2026, 6, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    result = parse_bot_response("请等待 32 分钟后再来签到", now=now)

    assert result.status == "deferred"
    assert result.next_eligible_at == now + timedelta(minutes=32)


def test_parse_success_response():
    result = parse_bot_response("✅ 今日已签到\n🔥 当前连签：8 天")

    assert result.status == "success"
    assert result.next_eligible_at is None


def test_parse_unknown_response():
    result = parse_bot_response("Unexpected reply from bot")

    assert result.status == "unknown"
    assert result.next_eligible_at is None

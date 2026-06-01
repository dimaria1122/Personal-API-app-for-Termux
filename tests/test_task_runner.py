from datetime import datetime

from zoneinfo import ZoneInfo

from src.task_runner import build_status_report, run_task_for_account


class FakeTransport:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def send_command(self, account, task):
        self.calls.append((account["name"], task["name"]))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_success_updates_last_success_and_clears_error():
    state = {}
    account = {"name": "main", "session": "account_1"}
    task = {"name": "midnight_bot", "bot": "@example_bot", "command": "/checkin"}
    now = datetime(2026, 6, 1, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    result = run_task_for_account(account, task, state, FakeTransport("✅ 今日已签到"), now=now)

    assert result.succeeded
    assert result.parsed_response.status == "success"
    assert state["main:midnight_bot"]["failure_count"] == 0
    assert state["main:midnight_bot"]["last_error"] is None
    assert state["main:midnight_bot"]["last_success_date"] == "2026-06-01"


def test_failure_increments_failure_count_and_records_error():
    state = {}
    account = {"name": "main", "session": "account_1"}
    task = {"name": "midnight_bot", "bot": "@example_bot", "command": "/checkin"}
    now = datetime(2026, 6, 1, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    result = run_task_for_account(account, task, state, FakeTransport(RuntimeError("network timeout")), now=now)

    assert not result.succeeded
    assert state["main:midnight_bot"]["failure_count"] == 1
    assert "network timeout" in state["main:midnight_bot"]["last_error"]


def test_deferred_response_updates_next_eligible_at_without_failure():
    state = {}
    account = {"name": "main", "session": "account_1"}
    task = {"name": "dw759_interval", "bot": "@example_bot", "command": "/sign"}
    now = datetime(2026, 6, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    result = run_task_for_account(
        account,
        task,
        state,
        FakeTransport("⏳ 签到太频繁啦！请等待 4 小时 32 分钟后再来签到。"),
        now=now,
    )

    assert not result.succeeded
    assert result.parsed_response.status == "deferred"
    assert state["main:dw759_interval"]["failure_count"] == 0
    assert state["main:dw759_interval"]["last_error"] is None
    assert state["main:dw759_interval"]["next_eligible_at"] == "2026-06-01T16:32:00+08:00"


def test_status_report_is_human_readable():
    report = build_status_report(
        {
            "main:midnight_bot": {
                "last_success_at": "2026-06-01T08:00:00+08:00",
                "failure_count": 0,
                "last_error": None,
            }
        }
    )

    assert "main:midnight_bot" in report
    assert "last_success_at=2026-06-01T08:00:00+08:00" in report

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.control_bot import (
    build_control_keyboard,
    is_allowed_user,
    parse_allowed_user_ids,
    parse_allowed_usernames,
    _ensure_session_dir,
    run_scheduler_once,
)


def test_parse_allowed_lists_normalizes_ids_and_usernames():
    assert parse_allowed_user_ids("1001, 1002 1003") == {1001, 1002, 1003}
    assert parse_allowed_usernames("@Alice, bob, , @CHARLIE") == {"alice", "bob", "charlie"}


def test_is_allowed_user_accepts_id_or_username_match():
    assert is_allowed_user(1001, "someone", {1001}, {"alice"})
    assert is_allowed_user(1002, "Alice", {1001}, {"alice"})
    assert not is_allowed_user(1002, "someone", {1001}, {"alice"})


def test_build_control_keyboard_exposes_expected_buttons():
    keyboard = build_control_keyboard()
    labels = [button.text for row in keyboard.inline_keyboard for button in row]

    assert labels == ["Run Now", "Dry Run", "Status"]


def test_ensure_session_dir_creates_missing_directory(workspace_tmp):
    session_dir = workspace_tmp / "control-bot"

    result = _ensure_session_dir(session_dir)

    assert result == session_dir
    assert session_dir.exists()
    assert session_dir.is_dir()


def test_run_scheduler_once_dry_run_reports_due_and_keeps_state_untouched(workspace_tmp):
    accounts_path = workspace_tmp / "accounts.yaml"
    tasks_path = workspace_tmp / "tasks.yaml"
    state_path = workspace_tmp / "state.json"

    accounts_path.write_text("accounts:\n  - name: main\n    session: account_1\n", encoding="utf-8")
    tasks_path.write_text(
        "tasks:\n"
        "  - name: midnight_bot\n"
        "    bot: '@freexzteam_bot'\n"
        "    command: /sign\n"
        "    accounts: [main]\n"
        "    schedule:\n"
        "      mode: calendar_day\n"
        "      timezone: Asia/Shanghai\n"
        "      earliest_time: '00:05'\n"
        "      random_delay_minutes: [0, 0]\n",
        encoding="utf-8",
    )

    lines = run_scheduler_once(
        accounts_path=accounts_path,
        tasks_path=tasks_path,
        state_path=state_path,
        now=datetime(2026, 6, 2, 0, 20, tzinfo=ZoneInfo("Asia/Shanghai")),
        dry_run=True,
    )

    assert lines == ["DUE main:midnight_bot"]
    assert not state_path.exists()

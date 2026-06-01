from src.__main__ import main


def test_status_command_prints_empty_state_message(workspace_tmp, capsys):
    state_path = workspace_tmp / "missing-state.json"

    exit_code = main(["status", "--state", str(state_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No task state recorded yet." in captured.out


def test_scheduler_dry_run_reports_due_task(workspace_tmp, capsys):
    accounts_path = workspace_tmp / "accounts.yaml"
    tasks_path = workspace_tmp / "tasks.yaml"
    state_path = workspace_tmp / "state.json"
    accounts_path.write_text("accounts:\n  - name: main\n    session: account_1\n", encoding="utf-8")
    tasks_path.write_text(
        "tasks:\n"
        "  - name: midnight_bot\n"
        "    bot: '@example_bot'\n"
        "    command: /checkin\n"
        "    accounts: [main]\n"
        "    schedule:\n"
        "      mode: calendar_day\n"
        "      timezone: Asia/Shanghai\n"
        "      earliest_time: '00:05'\n"
        "      random_delay_minutes: [0, 0]\n",
        encoding="utf-8",
    )
    state_path.write_text('{"main:midnight_bot": {"last_success_date": "2026-06-01"}}', encoding="utf-8")

    exit_code = main(
        [
            "scheduler",
            "--accounts",
            str(accounts_path),
            "--config",
            str(tasks_path),
            "--state",
            str(state_path),
            "--now",
            "2026-06-02T00:20:00+08:00",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "DUE main:midnight_bot" in captured.out

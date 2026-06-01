import pytest

from src.config_loader import ConfigError, load_accounts, load_tasks


def test_load_accounts_reads_account_aliases(workspace_tmp):
    path = workspace_tmp / "accounts.yaml"
    path.write_text(
        "accounts:\n"
        "  - name: main\n"
        "    phone: '+8613800000000'\n"
        "    session: account_1\n",
        encoding="utf-8",
    )

    accounts = load_accounts(path)

    assert accounts == [{"name": "main", "phone": "+8613800000000", "session": "account_1"}]


def test_load_tasks_reads_schedule_mode(workspace_tmp):
    path = workspace_tmp / "tasks.yaml"
    path.write_text(
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

    tasks = load_tasks(path)

    assert tasks[0]["name"] == "midnight_bot"
    assert tasks[0]["schedule"]["mode"] == "calendar_day"


def test_load_accounts_rejects_missing_accounts_key(workspace_tmp):
    path = workspace_tmp / "accounts.yaml"
    path.write_text("wrong: []\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="accounts"):
        load_accounts(path)

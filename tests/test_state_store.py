from src.state_store import load_state, save_state, state_key


def test_load_state_returns_empty_dict_when_file_is_missing(workspace_tmp):
    assert load_state(workspace_tmp / "state.json") == {}


def test_state_round_trip_preserves_task_records(workspace_tmp):
    path = workspace_tmp / "state.json"
    state = {
        "main:midnight_bot": {
            "last_success_at": "2026-06-01T08:00:00+08:00",
            "last_success_date": "2026-06-01",
            "failure_count": 0,
            "last_error": None,
        }
    }

    save_state(path, state)

    assert load_state(path) == state


def test_state_key_joins_account_and_task_names():
    assert state_key("main", "midnight_bot") == "main:midnight_bot"

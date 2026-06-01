from __future__ import annotations

import json
from pathlib import Path


def state_key(account_name: str, task_name: str) -> str:
    return f"{account_name}:{task_name}"


def load_state(path: str | Path) -> dict:
    state_path = Path(path)
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(path: str | Path, state: dict) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

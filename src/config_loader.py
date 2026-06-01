from __future__ import annotations

from pathlib import Path

import yaml


class ConfigError(ValueError):
    pass


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    return data


def _load_items(path: Path, key: str) -> list[dict]:
    data = _load_yaml(Path(path))
    items = data.get(key)
    if items is None:
        raise ConfigError(f"{path} is missing required key: {key}")
    if not isinstance(items, list):
        raise ConfigError(f"{path} key {key} must be a list")
    normalized: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            raise ConfigError(f"{path} key {key} must contain mappings")
        normalized.append(item)
    return normalized


def load_accounts(path: str | Path) -> list[dict]:
    return _load_items(Path(path), "accounts")


def load_tasks(path: str | Path) -> list[dict]:
    return _load_items(Path(path), "tasks")

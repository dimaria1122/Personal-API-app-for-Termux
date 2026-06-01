from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PUBLIC_API_ENV = Path("config/public-api.env")


@dataclass(frozen=True, slots=True)
class ApiCredentials:
    api_id: int
    api_hash: str


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = shlex.split(value.strip())[0] if value.strip() else ""
    return values


def load_api_credentials(public_env_path: str | Path = DEFAULT_PUBLIC_API_ENV) -> ApiCredentials:
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        fallback = _read_env_file(Path(public_env_path))
        api_id = api_id or fallback.get("TELEGRAM_API_ID")
        api_hash = api_hash or fallback.get("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        raise RuntimeError("Set TELEGRAM_API_ID and TELEGRAM_API_HASH, or keep config/public-api.env available.")
    return ApiCredentials(api_id=int(api_id), api_hash=api_hash)

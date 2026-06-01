from __future__ import annotations

from pathlib import Path


class BackendUnavailableError(RuntimeError):
    pass


def _load_pyrogram():
    try:
        from pyrogram import Client
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise BackendUnavailableError(
            "pyrogram is not installed. Install requirements.txt in Termux before using the Telegram backend."
        ) from exc
    return Client


class PyrogramTransport:
    def __init__(self, api_id: int, api_hash: str, sessions_dir: str | Path):
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._client_cls = _load_pyrogram()

    def _client(self, session_name: str):
        return self._client_cls(
            name=session_name,
            api_id=self.api_id,
            api_hash=self.api_hash,
            workdir=str(self.sessions_dir),
        )

    def login_account(self, account: dict) -> None:
        with self._client(account["session"]) as app:
            app.get_me()

    def send_command(self, account: dict, task: dict) -> str:
        with self._client(account["session"]) as app:
            app.send_message(task["bot"], task["command"])
        return "sent"

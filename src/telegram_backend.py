from __future__ import annotations

from pathlib import Path
import time


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
            sent = app.send_message(task["bot"], task["command"])
            return self._wait_for_response(app, task["bot"], sent.id)

    def _wait_for_response(self, app, chat_id: str, after_message_id: int, timeout_seconds: int = 20) -> str:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            for message in app.get_chat_history(chat_id, limit=10):
                if message.id <= after_message_id:
                    break
                if message.text:
                    return message.text
            time.sleep(2)
        return ""

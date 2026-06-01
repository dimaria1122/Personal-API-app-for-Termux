from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from src.config_loader import load_accounts, load_tasks
from src.credentials import load_api_credentials
from src.scheduler import is_task_due
from src.state_store import load_state, save_state


@dataclass(frozen=True, slots=True)
class ControlButton:
    text: str
    callback_data: str


@dataclass(frozen=True, slots=True)
class ControlKeyboard:
    inline_keyboard: list[list[ControlButton]]


def _load_pyrogram():
    try:
        from pyrogram import Client, filters, idle
        from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("Install requirements.txt before running the control bot.") from exc
    return Client, filters, idle, InlineKeyboardButton, InlineKeyboardMarkup


def parse_allowed_user_ids(value: str | None) -> set[int]:
    if not value:
        return set()
    result: set[int] = set()
    for part in value.replace(",", " ").split():
        item = part.strip()
        if item:
            result.add(int(item))
    return result


def parse_allowed_usernames(value: str | None) -> set[str]:
    if not value:
        return set()
    result: set[str] = set()
    for part in value.replace(",", " ").split():
        item = part.strip().lstrip("@").lower()
        if item:
            result.add(item)
    return result


def is_allowed_user(
    user_id: int | None,
    username: str | None,
    allowed_ids: set[int],
    allowed_usernames: set[str],
) -> bool:
    if user_id is not None and user_id in allowed_ids:
        return True
    if username and username.lower() in allowed_usernames:
        return True
    return False


def build_control_keyboard() -> ControlKeyboard:
    return ControlKeyboard(
        inline_keyboard=[
            [
                ControlButton("Run Now", "control:run_now"),
                ControlButton("Dry Run", "control:dry_run"),
                ControlButton("Status", "control:status"),
            ]
        ]
    )


def _to_pyrogram_keyboard(keyboard: ControlKeyboard):
    _, _, _, InlineKeyboardButton, InlineKeyboardMarkup = _load_pyrogram()
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(button.text, callback_data=button.callback_data) for button in row]
            for row in keyboard.inline_keyboard
        ]
    )


def _parse_now(value: str | None) -> datetime:
    if value:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.astimezone()
        return parsed
    return datetime.now().astimezone()


def _default_account_map(accounts: list[dict]) -> dict[str, dict]:
    return {account["name"]: account for account in accounts}


def _build_transport(account_dir: str | Path):
    credentials = load_api_credentials()
    from src.telegram_backend import PyrogramTransport

    return PyrogramTransport(api_id=credentials.api_id, api_hash=credentials.api_hash, sessions_dir=account_dir)


def _ensure_session_dir(session_dir: str | Path) -> Path:
    path = Path(session_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_scheduler_once(
    *,
    accounts_path: str | Path,
    tasks_path: str | Path,
    state_path: str | Path,
    now: datetime | None = None,
    dry_run: bool,
) -> list[str]:
    accounts = _default_account_map(load_accounts(accounts_path))
    tasks = load_tasks(tasks_path)
    state = load_state(state_path)
    current = now or datetime.now().astimezone()
    due_lines: list[str] = []
    transport = None
    if not dry_run:
        transport = _build_transport(Path(state_path).parent / "sessions")
        from src.task_runner import run_task_for_account

    for task in tasks:
        for account_name in task.get("accounts", []):
            account = accounts.get(account_name)
            if account is None:
                due_lines.append(f"SKIP {account_name}:{task['name']} missing-account")
                continue
            record = state.get(f"{account_name}:{task['name']}", {})
            if is_task_due(current, account_name, task, record):
                due_lines.append(f"DUE {account_name}:{task['name']}")
                if transport is not None:
                    run_task_for_account(account, task, state, transport, now=current)
            else:
                due_lines.append(f"SKIP {account_name}:{task['name']} not-due")
    if not dry_run:
        save_state(state_path, state)
    return due_lines


def _status_text(state_path: str | Path) -> str:
    from src.task_runner import build_status_report

    return build_status_report(load_state(state_path))


def _deny(message, text: str) -> None:  # noqa: ANN001
    message.reply_text(text)


def _ack_callback(query, *, text: str | None = None, show_alert: bool = False) -> None:  # noqa: ANN001
    try:
        if text is None:
            query.answer()
        else:
            query.answer(text, show_alert=show_alert)
    except Exception:  # noqa: BLE001
        return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="teleg-control-bot")
    parser.add_argument("--accounts", default="config/accounts.yaml")
    parser.add_argument("--tasks", default="config/tasks.yaml")
    parser.add_argument("--state", default="data/state.json")
    parser.add_argument("--now")
    parser.add_argument("--session-dir", default="data/control-bot")
    args = parser.parse_args(argv)

    allowed_ids = parse_allowed_user_ids(os.environ.get("CONTROL_ALLOWED_USER_IDS"))
    allowed_usernames = parse_allowed_usernames(os.environ.get("CONTROL_ALLOWED_USERNAMES"))
    if not allowed_ids and not allowed_usernames:
        raise RuntimeError("Set CONTROL_ALLOWED_USER_IDS or CONTROL_ALLOWED_USERNAMES before starting the control bot.")

    token = os.environ.get("CONTROL_BOT_TOKEN") or os.environ.get("TELEGRAM_CONTROL_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set CONTROL_BOT_TOKEN from BotFather before starting the control bot.")

    session_dir = _ensure_session_dir(args.session_dir)
    credentials = load_api_credentials()
    Client, filters, idle, _, _ = _load_pyrogram()
    app = Client(
        "control-bot",
        api_id=credentials.api_id,
        api_hash=credentials.api_hash,
        bot_token=token,
        workdir=str(session_dir),
    )

    keyboard = _to_pyrogram_keyboard(build_control_keyboard())

    def _authorized(user) -> bool:  # noqa: ANN001
        return is_allowed_user(getattr(user, "id", None), getattr(user, "username", None), allowed_ids, allowed_usernames)

    @app.on_message(filters.private)
    def _on_message(_, message):  # noqa: ANN001
        if not _authorized(message.from_user):
            return _deny(message, "Access denied.")
        if not getattr(message, "text", ""):
            return _deny(message, "Use the buttons below.")
        if message.text.startswith("/start") or message.text.startswith("/help"):
            return message.reply_text("Control bot ready.", reply_markup=keyboard)
        if message.text.startswith("/status"):
            return message.reply_text(_status_text(args.state), reply_markup=keyboard)
        return message.reply_text("Use the buttons below.", reply_markup=keyboard)

    @app.on_callback_query()
    def _on_callback(_, query):  # noqa: ANN001
        if not _authorized(query.from_user):
            return _ack_callback(query, text="Access denied.", show_alert=True)

        action = getattr(query, "data", "")
        _ack_callback(query, text="Working...")
        if action == "control:status":
            text = _status_text(args.state)
        elif action == "control:dry_run":
            text = "\n".join(
                run_scheduler_once(
                    accounts_path=args.accounts,
                    tasks_path=args.tasks,
                    state_path=args.state,
                    now=_parse_now(args.now),
                    dry_run=True,
                )
            )
        elif action == "control:run_now":
            text = "\n".join(
                run_scheduler_once(
                    accounts_path=args.accounts,
                    tasks_path=args.tasks,
                    state_path=args.state,
                    now=_parse_now(args.now),
                    dry_run=False,
                )
            )
        else:
            text = "Unknown action."
        if not text:
            text = "No output."
        query.message.reply_text(text[:3500], reply_markup=keyboard)

    with app:
        idle()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

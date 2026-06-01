from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from src.config_loader import load_accounts, load_tasks
from src.credentials import load_api_credentials
from src.scheduler import is_task_due
from src.state_store import load_state, save_state
from src.task_runner import build_status_report, run_task_for_account


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


def _cmd_status(args) -> int:
    state = load_state(args.state)
    print(build_status_report(state))
    return 0


def _cmd_scheduler(args) -> int:
    accounts = _default_account_map(load_accounts(args.accounts))
    tasks = load_tasks(args.config)
    state = load_state(args.state)
    now = _parse_now(args.now)
    due_lines: list[str] = []
    transport = None
    if not args.dry_run:
        transport = _build_transport(Path(args.state).parent / "sessions")
    for task in tasks:
        for account_name in task.get("accounts", []):
            account = accounts.get(account_name)
            if account is None:
                due_lines.append(f"SKIP {account_name}:{task['name']} missing-account")
                continue
            record = state.get(f"{account_name}:{task['name']}", {})
            if is_task_due(now, account_name, task, record):
                due_lines.append(f"DUE {account_name}:{task['name']}")
                if transport is not None:
                    run_task_for_account(account, task, state, transport, now=now)
            else:
                due_lines.append(f"SKIP {account_name}:{task['name']} not-due")
    if not args.dry_run:
        save_state(args.state, state)
    print("\n".join(due_lines))
    return 0


def _cmd_login(args) -> int:
    accounts = load_accounts(args.accounts)
    transport = _build_transport(Path(args.sessions_dir))
    for account in accounts:
        transport.login_account(account)
        print(f"LOGGED_IN {account['name']}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="teleg-sign")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--state", default="data/state.json")
    status_parser.set_defaults(func=_cmd_status)

    scheduler_parser = subparsers.add_parser("scheduler")
    scheduler_parser.add_argument("--accounts", default="config/accounts.yaml")
    scheduler_parser.add_argument("--config", default="config/tasks.yaml")
    scheduler_parser.add_argument("--state", default="data/state.json")
    scheduler_parser.add_argument("--now")
    scheduler_parser.add_argument("--dry-run", action="store_true")
    scheduler_parser.set_defaults(func=_cmd_scheduler)

    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("--accounts", default="config/accounts.yaml")
    login_parser.add_argument("--sessions-dir", default="data/sessions")
    login_parser.set_defaults(func=_cmd_login)

    control_parser = subparsers.add_parser("control-bot")
    control_parser.set_defaults(func=_cmd_control_bot)

    args = parser.parse_args(argv)
    return args.func(args)


def _cmd_control_bot(args) -> int:
    from src.control_bot import main as control_main

    return control_main([])


if __name__ == "__main__":
    raise SystemExit(main())

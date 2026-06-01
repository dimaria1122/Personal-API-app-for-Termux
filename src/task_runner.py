from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.state_store import state_key
from src.response_parser import ResponseParseResult, evaluate_bot_response


@dataclass(slots=True)
class TaskRunResult:
    succeeded: bool
    status: str
    message: str = ""
    next_eligible_at: str | None = None
    parsed_response: ResponseParseResult | None = None


def run_task_for_account(account: dict, task: dict, state: dict, transport, now: datetime | None = None) -> TaskRunResult:
    key = state_key(account["name"], task["name"])
    record = state.setdefault(
        key,
        {
            "failure_count": 0,
            "last_error": None,
            "last_success_at": None,
            "last_success_date": None,
            "next_eligible_at": None,
        },
    )
    now = now or datetime.now().astimezone()
    try:
        message = transport.send_command(account, task)
    except Exception as exc:  # noqa: BLE001
        record["failure_count"] = int(record.get("failure_count", 0)) + 1
        record["last_error"] = str(exc)
        record["next_eligible_at"] = None
        return TaskRunResult(False, status="error", message=str(exc))

    evaluation = evaluate_bot_response(message, now=now)
    if evaluation.status == "deferred":
        record["failure_count"] = 0
        record["last_error"] = None
        record["next_eligible_at"] = (
            evaluation.next_eligible_at.isoformat() if evaluation.next_eligible_at else None
        )
        return TaskRunResult(
            False,
            status="deferred",
            message=message,
            next_eligible_at=record["next_eligible_at"],
            parsed_response=evaluation,
        )

    if evaluation.status == "success":
        record["failure_count"] = 0
        record["last_error"] = None
        record["next_eligible_at"] = None
        record["last_success_at"] = now.isoformat()
        record["last_success_date"] = now.date().isoformat()
        return TaskRunResult(True, status="success", message=str(message or "ok"), parsed_response=evaluation)

    record["failure_count"] = int(record.get("failure_count", 0)) + 1
    record["last_error"] = f"unrecognized response: {message}"
    record["next_eligible_at"] = None
    return TaskRunResult(False, status="unknown", message=message, parsed_response=evaluation)


def build_status_report(state: dict) -> str:
    if not state:
        return "No task state recorded yet."
    lines: list[str] = []
    for key, record in sorted(state.items()):
        parts = [key]
        if record.get("last_success_at"):
            parts.append(f"last_success_at={record['last_success_at']}")
        if record.get("last_success_date"):
            parts.append(f"last_success_date={record['last_success_date']}")
        if record.get("next_eligible_at"):
            parts.append(f"next_eligible_at={record['next_eligible_at']}")
        parts.append(f"failure_count={record.get('failure_count', 0)}")
        if record.get("last_error"):
            parts.append(f"last_error={record['last_error']}")
        lines.append(" ".join(parts))
    return "\n".join(lines)

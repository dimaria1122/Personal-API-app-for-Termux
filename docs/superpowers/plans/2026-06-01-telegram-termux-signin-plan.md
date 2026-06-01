# Telegram Termux Sign-In Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a phone-first Telegram auto sign-in runner for three personal accounts on Android Termux, with support for both midnight-based and last-success-based bot schedules.

**Architecture:** Start with a minimal Python project that wraps an existing Telegram userbot/sign-in library rather than reimplementing Telegram client logic. Add a small scheduler, YAML config loader, JSON state store, and Termux helper scripts. Validate runtime compatibility with TG-SignPulse first; if that is too brittle, fall back to tg-signer behavior or a minimal Pyrogram/Telethon runner only for the required sign-in flows.

**Tech Stack:** Python 3, Termux, YAML config, JSON state, Telegram userbot library already used by TG-SignPulse or tg-signer, shell scripts for Termux setup.

---

### Task 1: Establish the project skeleton and mobile setup docs

**Files:**
- Create: `README.md`
- Create: `config/accounts.example.yaml`
- Create: `config/tasks.example.yaml`
- Create: `scripts/setup_termux.sh`
- Create: `scripts/run_scheduler.sh`
- Create: `scripts/login_accounts.sh`
- Create: `scripts/check_status.sh`
- Create: `src/__init__.py`
- Create: `src/config_loader.py`
- Create: `src/state_store.py`
- Create: `src/scheduler.py`
- Create: `src/task_runner.py`

- [ ] **Step 1: Create the minimal project layout and runtime entrypoints**

```text
teleg-sign/
  config/
  data/
    logs/
    sessions/
  scripts/
  src/
```

- [ ] **Step 2: Add a Termux-first README with installation and background notes**

```markdown
# Telegram Termux Sign-In

## Setup

1. Install Termux from F-Droid.
2. In Termux, run `bash scripts/setup_termux.sh`.
3. Copy `config/accounts.example.yaml` to `config/accounts.yaml`.
4. Copy `config/tasks.example.yaml` to `config/tasks.yaml`.
5. Run `bash scripts/login_accounts.sh` to create Telegram sessions.
6. Run `bash scripts/run_scheduler.sh` to start sign-in scheduling.

## Phone stability

- Disable battery optimization for Termux.
- Allow background activity and autostart.
- Lock Termux in recents if the phone UI supports it.
- Use `termux-wake-lock` before long-running scheduling.

## Scheduling modes

- `calendar_day`: eligible after local midnight and the configured earliest time.
- `interval_after_success`: eligible only after the previous success time plus the configured interval.
```

- [ ] **Step 3: Create example configs that show both schedule modes**

```yaml
# config/accounts.example.yaml
accounts:
  - name: main
    phone: "+86xxxxxxxxxxx"
    session: "account_1"
  - name: alt1
    phone: "+86xxxxxxxxxxx"
    session: "account_2"
  - name: alt2
    phone: "+86xxxxxxxxxxx"
    session: "account_3"
```

```yaml
# config/tasks.example.yaml
tasks:
  - name: midnight_bot
    bot: "@example_midnight_bot"
    command: "/checkin"
    accounts: ["main", "alt1", "alt2"]
    schedule:
      mode: calendar_day
      timezone: Asia/Shanghai
      earliest_time: "00:05"
      random_delay_minutes: [5, 45]

  - name: interval_bot
    bot: "@example_interval_bot"
    command: "/checkin"
    accounts: ["main", "alt1", "alt2"]
    schedule:
      mode: interval_after_success
      min_interval_hours: 24
      random_delay_minutes: [5, 40]
```

- [ ] **Step 4: Add shell wrappers that will later call the Python entrypoints**

```bash
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
python -m src.scheduler --config config/tasks.yaml --accounts config/accounts.yaml
```

```bash
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
python -m src.task_runner login --accounts config/accounts.yaml
```

```bash
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
python -m src.task_runner status --state data/state.json --logs data/logs
```

- [ ] **Step 5: Add a bootstrap script for Termux dependencies**

```bash
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
pkg update -y
pkg install -y python git termux-api
python -m pip install --upgrade pip
python -m pip install pyyaml
```

- [ ] **Step 6: Run the shell files through syntax checks**

Run:

```bash
bash -n scripts/setup_termux.sh
bash -n scripts/run_scheduler.sh
bash -n scripts/login_accounts.sh
bash -n scripts/check_status.sh
```

Expected: no syntax errors.

### Task 2: Implement config loading and state storage

**Files:**
- Modify: `src/config_loader.py`
- Modify: `src/state_store.py`
- Create: `tests/test_config_loader.py`
- Create: `tests/test_state_store.py`

- [ ] **Step 1: Write the failing tests for config parsing and state persistence**

```python
from pathlib import Path

from src.config_loader import load_accounts, load_tasks
from src.state_store import load_state, save_state


def test_load_accounts_and_tasks(tmp_path):
    accounts_path = tmp_path / "accounts.yaml"
    tasks_path = tmp_path / "tasks.yaml"
    accounts_path.write_text("accounts:\n  - name: main\n    session: account_1\n", encoding="utf-8")
    tasks_path.write_text(
        "tasks:\n"
        "  - name: midnight_bot\n"
        "    bot: '@example_bot'\n"
        "    command: /checkin\n"
        "    accounts: [main]\n"
        "    schedule:\n"
        "      mode: calendar_day\n"
        "      timezone: Asia/Shanghai\n"
        "      earliest_time: '00:05'\n",
        encoding="utf-8",
    )

    assert load_accounts(accounts_path)[0]["name"] == "main"
    assert load_tasks(tasks_path)[0]["schedule"]["mode"] == "calendar_day"


def test_state_round_trip(tmp_path):
    state_path = tmp_path / "state.json"
    state = {"main:midnight_bot": {"failure_count": 0, "last_error": None}}

    save_state(state_path, state)

    assert load_state(state_path) == state
```

- [ ] **Step 2: Run the tests to confirm they fail before implementation**

Run:

```bash
pytest tests/test_config_loader.py tests/test_state_store.py -v
```

Expected: import or assertion failures.

- [ ] **Step 3: Implement YAML loading and JSON state read/write**

```python
from pathlib import Path

import yaml


def load_accounts(path):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return data.get("accounts", [])


def load_tasks(path):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return data.get("tasks", [])


def load_state(path):
    state_path = Path(path)
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(path, state):
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Run the tests again**

Run:

```bash
pytest tests/test_config_loader.py tests/test_state_store.py -v
```

Expected: pass.

- [ ] **Step 5: Commit the config/state foundation**

```bash
git add src/config_loader.py src/state_store.py tests/test_config_loader.py tests/test_state_store.py
git commit -m "feat: add config and state storage"
```

### Task 3: Add scheduling logic for both bot timing rules

**Files:**
- Modify: `src/scheduler.py`
- Create: `tests/test_scheduler.py`

- [ ] **Step 1: Write tests for `calendar_day` and `interval_after_success` eligibility**

```python
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.scheduler import is_due_calendar_day, is_due_interval_after_success


def test_calendar_day_becomes_eligible_after_midnight():
    now = datetime(2026, 6, 2, 0, 20, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert is_due_calendar_day(
        now=now,
        last_success_date="2026-06-01",
        timezone="Asia/Shanghai",
        earliest_time="00:05",
        random_delay_minutes=[0, 0],
    )


def test_interval_after_success_waits_full_interval():
    now = datetime(2026, 6, 2, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    last_success_at = "2026-06-01T09:30:00+08:00"

    assert not is_due_interval_after_success(
        now=now,
        last_success_at=last_success_at,
        min_interval_hours=24,
        random_delay_minutes=[0, 0],
    )
```

- [ ] **Step 2: Run the scheduler tests and confirm they fail first**

Run:

```bash
pytest tests/test_scheduler.py -v
```

Expected: failures due to missing eligibility functions.

- [ ] **Step 3: Implement the due-time calculation helpers**

```python
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


def is_due_calendar_day(now, last_success_date, timezone, earliest_time, random_delay_minutes):
    local_now = now.astimezone(ZoneInfo(timezone))
    if last_success_date == local_now.date().isoformat():
        return False
    hour, minute = [int(part) for part in earliest_time.split(":", 1)]
    earliest = datetime.combine(local_now.date(), time(hour, minute), tzinfo=ZoneInfo(timezone))
    return local_now >= earliest + timedelta(minutes=random_delay_minutes[0])


def is_due_interval_after_success(now, last_success_at, min_interval_hours, random_delay_minutes):
    if not last_success_at:
        return True
    last_success = datetime.fromisoformat(last_success_at)
    next_due = last_success + timedelta(hours=min_interval_hours, minutes=random_delay_minutes[0])
    return now >= next_due
```

- [ ] **Step 4: Run the scheduler tests again**

Run:

```bash
pytest tests/test_scheduler.py -v
```

Expected: pass.

- [ ] **Step 5: Commit the scheduler logic**

```bash
git add src/scheduler.py tests/test_scheduler.py
git commit -m "feat: add sign-in scheduling rules"
```

### Task 4: Build the account task runner and status reporting

**Files:**
- Modify: `src/task_runner.py`
- Create: `tests/test_task_runner.py`

- [ ] **Step 1: Write tests for running one task against one account and updating state**

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from src.task_runner import build_status_report, run_task_for_account


class FakeTransport:
    def __init__(self, result):
        self.result = result

    def send_command(self, account, task):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_success_updates_last_success_and_clears_error():
    state = {}
    account = {"name": "main", "session": "account_1"}
    task = {"name": "midnight_bot", "bot": "@example", "command": "/checkin"}

    run_task_for_account(account, task, state, FakeTransport("ok"), now=datetime(2026, 6, 1, 8, tzinfo=ZoneInfo("Asia/Shanghai")))

    record = state["main:midnight_bot"]
    assert record["failure_count"] == 0
    assert record["last_error"] is None
    assert record["last_success_date"] == "2026-06-01"


def test_failure_increments_failure_count_and_records_error():
    state = {}
    account = {"name": "main", "session": "account_1"}
    task = {"name": "midnight_bot", "bot": "@example", "command": "/checkin"}

    run_task_for_account(account, task, state, FakeTransport(RuntimeError("network timeout")), now=datetime(2026, 6, 1, 8, tzinfo=ZoneInfo("Asia/Shanghai")))

    record = state["main:midnight_bot"]
    assert record["failure_count"] == 1
    assert "network timeout" in record["last_error"]
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run:

```bash
pytest tests/test_task_runner.py -v
```

Expected: failures before implementation.

- [ ] **Step 3: Implement the runner state transitions and status summary output**

```python
from datetime import datetime


def run_task_for_account(account, task, state, transport, now=None):
    key = f"{account['name']}:{task['name']}"
    record = state.setdefault(key, {"failure_count": 0, "last_error": None})
    now = now or datetime.now().astimezone()
    try:
        transport.send_command(account, task)
    except Exception as exc:
        record["failure_count"] = int(record.get("failure_count", 0)) + 1
        record["last_error"] = str(exc)
        return False
    record["failure_count"] = 0
    record["last_error"] = None
    record["last_success_at"] = now.isoformat()
    record["last_success_date"] = now.date().isoformat()
    return True


def build_status_report(state):
    if not state:
        return "No task state recorded yet."
    return "\n".join(f"{key}: failures={value.get('failure_count', 0)} error={value.get('last_error')}" for key, value in sorted(state.items()))
```

- [ ] **Step 4: Run the tests again**

Run:

```bash
pytest tests/test_task_runner.py -v
```

Expected: pass.

- [ ] **Step 5: Commit the runner and status output**

```bash
git add src/task_runner.py tests/test_task_runner.py
git commit -m "feat: add task runner state transitions"
```

### Task 5: Validate TG-SignPulse in Termux and decide the runtime backend

**Files:**
- Create: `docs/runtime-validation.md`
- Modify: `README.md`
- Modify: `scripts/setup_termux.sh`

- [ ] **Step 1: Document the exact Termux validation commands**

```markdown
## Validate TG-SignPulse

1. Install the dependencies from `scripts/setup_termux.sh`.
2. Clone TG-SignPulse into a temporary directory.
3. Run its install or startup command inside Termux.
4. Record whether dependency resolution, session creation, and a dry-run sign-in succeed.
```

- [ ] **Step 2: Add the validation notes to the README**

```markdown
## Backend choice

If TG-SignPulse runs cleanly in Termux, use it as the backend.
If not, switch to tg-signer behavior or a minimal userbot runner for the same schedule model.
```

- [ ] **Step 3: Capture the runtime outcome in a local doc**

```markdown
# Runtime validation

- Result: not yet run on device
- Reason: waiting for Termux validation on the iQOO 12
- Follow-up: run the commands in this document and replace this section with pass, fail, or blocked
```

- [ ] **Step 4: Commit the validation docs**

```bash
git add README.md docs/runtime-validation.md scripts/setup_termux.sh
git commit -m "docs: record Termux backend validation path"
```

### Task 6: Wire the CLI entrypoints and smoke test them in Termux

**Files:**
- Create or modify: `src/__main__.py`
- Modify: `scripts/run_scheduler.sh`
- Modify: `scripts/login_accounts.sh`
- Modify: `scripts/check_status.sh`

- [ ] **Step 1: Add CLI dispatch for login, run, and status commands**

```python
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(prog="teleg-sign")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("scheduler")
    subparsers.add_parser("login")
    args = parser.parse_args(argv)
    return args.command
```

- [ ] **Step 2: Run the CLI help and status command**

Run:

```bash
python -m src --help
python -m src status --state data/state.json --logs data/logs
```

Expected: command help prints and status succeeds with empty/default state.

- [ ] **Step 3: Run a dry scheduler invocation with sample config**

Run:

```bash
python -m src scheduler --config config/tasks.yaml --accounts config/accounts.yaml --dry-run
```

Expected: it prints which tasks would run and which are not due.

- [ ] **Step 4: Commit the CLI wiring**

```bash
git add src/__main__.py scripts/run_scheduler.sh scripts/login_accounts.sh scripts/check_status.sh
git commit -m "feat: add Termux CLI entrypoints"
```

## Coverage Check

- `calendar_day` scheduling: Task 3.
- `interval_after_success` scheduling: Task 3.
- Three account sessions: Task 1 and Task 4.
- Phone-first Termux setup: Task 1 and Task 5.
- TG-SignPulse reuse decision: Task 5.
- Logs and status: Task 4 and Task 6.
- Minimal, no Web UI: enforced by Tasks 1-6 and out-of-scope section in the spec.

## Gaps To Watch

- If TG-SignPulse cannot run in Termux, Task 5 must decide whether tg-signer or a minimal replacement is the backend.
- If a bot flow is interactive or variable, Task 4 may need a small adapter interface for bot-specific action sequences.
- If Android background behavior is too unstable, the README may need stronger operational guidance, but the code should stay unchanged.

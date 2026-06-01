# Telegram Termux Auto Sign-In Design

## Objective

Build a phone-first Telegram auto sign-in setup for three personal Telegram accounts on an iQOO 12 Android phone. The first version will run inside Termux and reuse existing open-source Telegram userbot/sign-in tooling where practical, with small project-specific wrappers for configuration, scheduling, logging, and phone setup.

The system is intended for the user's own accounts and normal daily sign-in flows. It will not bypass CAPTCHA, account risk checks, human verification, bans, or Telegram anti-abuse mechanisms.

## Chosen Approach

Use Termux on Android with a Python-based Telegram sign-in runner, based on TG-SignPulse or its upstream tg-signer behavior.

Reasons:

- It avoids keeping a Windows computer online.
- It avoids building a full native Android app for the first version.
- Existing projects already solve most Telegram client/session and bot interaction mechanics.
- It keeps development focused on the user's real differentiator: multi-account scheduling rules and phone-friendly operation.

## Alternatives Considered

1. VPS or Docker deployment.

This is usually more stable than a phone because servers stay online, but it requires a remote machine and initial Telegram login/session setup outside the phone. The user prefers a phone-local workflow.

2. Native Android app.

This would produce a more polished mobile experience but requires significantly more work: Telegram client integration, account session storage, Android background execution, logging UI, and update handling. It is not the right first version.

3. Direct Termux reuse of TG-SignPulse without wrappers.

This may work for simple bot schedules, but the user needs mixed scheduling rules across bots and three accounts. A thin scheduling/configuration layer is worth adding.

## Runtime Environment

The target device is an iQOO 12 Android phone.

Termux will be installed from F-Droid or another current trusted source. The setup will install:

- Python
- pip
- git
- Termux API support when needed

The phone setup instructions must include iQOO/vivo-style background stability steps:

- Disable battery optimization for Termux.
- Allow background activity.
- Allow autostart if available.
- Lock Termux in recent apps if the system supports it.
- Use `termux-wake-lock` when long-running scheduling is required.

The design assumes Android background execution may still be imperfect. Logging and status commands must make missed runs visible.

## Accounts

The system will manage three Telegram user accounts.

Each account logs in once and gets a separate local session file, for example:

- `account_1.session`
- `account_2.session`
- `account_3.session`

Configuration will refer to account aliases, not phone numbers or passwords. Sensitive session files stay under the local `data/sessions/` directory and must not be committed to git.

The runner should process accounts sequentially by default. It should not have all three accounts hit the same bot at the same instant.

## Sign-In Tasks

Each sign-in target is configured as a task. A task defines:

- Human-readable task name.
- Telegram bot username or chat target.
- Command or action flow to trigger sign-in.
- Accounts that should run this task.
- Scheduling mode.
- Retry policy.

Example configuration shape:

```yaml
accounts:
  - name: main
    session: account_1
  - name: alt1
    session: account_2
  - name: alt2
    session: account_3

tasks:
  - name: daily_midnight_bot
    bot: "@example_midnight_bot"
    command: "/checkin"
    accounts: ["main", "alt1", "alt2"]
    schedule:
      mode: calendar_day
      timezone: Asia/Shanghai
      earliest_time: "00:05"
      random_delay_minutes: [5, 45]

  - name: interval_based_bot
    bot: "@example_interval_bot"
    command: "/checkin"
    accounts: ["main", "alt1", "alt2"]
    schedule:
      mode: interval_after_success
      min_interval_hours: 24
      random_delay_minutes: [5, 40]
```

## Scheduling Rules

The first version must support two scheduling modes.

### `calendar_day`

Use this for bots that allow a new sign-in after the local date changes.

Rule:

- Track the last successful sign-in date per account and task.
- If the current date in the configured timezone is newer than `last_success_date`, the task is eligible.
- Do not run immediately at exactly 00:00. Use `earliest_time` plus a random delay window to reduce repeated mechanical timing.

This mode handles bots where "after midnight" is enough.

### `interval_after_success`

Use this for bots that require waiting until after the previous successful sign-in time.

Rule:

- Track `last_success_at` per account and task.
- Next eligible time is `last_success_at + min_interval_hours + random_delay`.
- If there is no previous success, allow the task to run during the next scheduler cycle, subject to optional startup delay.

This mode handles bots that require "after yesterday's sign-in time".

## State Storage

State will be stored locally, likely as JSON for the first version:

```json
{
  "main:daily_midnight_bot": {
    "last_success_at": "2026-06-01T00:42:00+08:00",
    "last_success_date": "2026-06-01",
    "last_error": null,
    "failure_count": 0
  }
}
```

State is keyed by account alias and task name. This keeps each account/task pair independent.

State files must be backed up carefully by the user if they matter, but they must not be committed.

## Retry And Failure Handling

Transient failures may retry a small number of times:

- Network timeout.
- Telegram temporary flood wait or rate response.
- Bot does not respond quickly.
- Termux process was paused and resumed.

Non-automatable failures must stop that task attempt and require manual attention:

- CAPTCHA.
- Human verification.
- Telegram login/security checkpoint.
- Account risk warning.
- Bot behavior changed in a way that no configured flow matches.

The runner must avoid aggressive retry loops. A reasonable default is one or two delayed retries, then mark the run failed and wait for the next scheduled opportunity.

## Logs And Status

The first version will not include a full Web UI.

It will provide:

- Plain log files under `data/logs/`.
- A status command that summarizes each account/task pair.
- Clear markers for success, skipped-not-due, retrying, and failed-needs-manual-check.

This is enough for Termux operation and keeps the first version small.

## Proposed Project Structure

```text
teleg-sign/
  config/
    accounts.yaml
    tasks.yaml
  data/
    sessions/
    state.json
    logs/
  scripts/
    setup_termux.sh
    login_accounts.sh
    run_scheduler.sh
    check_status.sh
  src/
    scheduler.py
    task_runner.py
    state_store.py
    config_loader.py
  README.md
```

## Open-Source Reuse Plan

The first implementation should evaluate TG-SignPulse and tg-signer integration in this order:

1. Try to run TG-SignPulse in Termux with minimal changes.
2. If TG-SignPulse is too heavy or not maintained enough for Termux, reuse tg-signer directly.
3. If both are difficult to embed cleanly, keep their behavior as references and build a small Pyrogram/Telethon-based runner only for the required sign-in flows.

The implementation should not clone or vendor code blindly until license and runtime fit are checked.

## Out Of Scope For Version 1

- Native Android app.
- Web dashboard.
- Cloud sync.
- CAPTCHA solving.
- Ban/risk-control bypass.
- Telegram abuse automation.
- Parallel high-frequency account activity.
- Complex visual flow editor.

## Acceptance Criteria

Version 1 is successful when:

- The user can install Termux dependencies on the iQOO 12 using documented steps.
- Three Telegram accounts can each create and reuse a separate session.
- The user can define multiple bot sign-in tasks in config files.
- Each task can choose either `calendar_day` or `interval_after_success` scheduling.
- Each account/task pair records last success, failure count, and last error independently.
- Logs clearly show whether a task succeeded, was skipped because it was not due, failed temporarily, or needs manual attention.
- The scheduler can run continuously in Termux with phone background setup documented.

## Risks

- Android may stop Termux despite battery settings.
- Some Telegram bots may require interactive verification that cannot be automated safely.
- TG-SignPulse may not run cleanly on current Termux without dependency fixes.
- Telegram user sessions are sensitive; losing the phone or leaking session files is a real account security risk.

## Self-Review Notes

This spec defines both required scheduling modes and keeps implementation scope limited to Termux plus a thin orchestration layer. It deliberately excludes CAPTCHA bypass and native Android work. The main unresolved implementation detail is whether TG-SignPulse can run directly in Termux; this will be handled in the implementation plan as an early validation checkpoint.

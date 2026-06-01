# Telegram Termux Sign-In

Chinese phone setup guide: [README_CN.md](README_CN.md)

Phone-first Telegram sign-in scheduler for personal accounts. The first version runs in Termux, stores local Telegram sessions, and supports two scheduling modes:

- `calendar_day`: the bot allows a new sign-in after the local date changes.
- `interval_after_success`: the bot requires waiting after the previous successful sign-in time.

This project is for your own Telegram accounts and normal sign-in flows. It does not bypass CAPTCHA, account risk checks, human verification, bans, or Telegram anti-abuse systems.

## Current Backend

The implementation uses a small Pyrogram backend for the first runnable version. TG-SignPulse and tg-signer remain useful references, but TG-SignPulse is archived and heavier than needed for the first Termux run.

## Termux Setup

In Termux, from the project directory:

```bash
bash scripts/setup_termux.sh
```

This repo includes a temporary public Telegram Desktop API identity in `config/public-api.env` so you can verify the phone workflow first.

When your own Telegram API application works, create a local override file:

```bash
cat > ~/.tg-sign.env <<'EOF'
export TELEGRAM_API_ID=123456
export TELEGRAM_API_HASH=0123456789abcdef0123456789abcdef
EOF
chmod 600 ~/.tg-sign.env
source ~/.tg-sign.env
```

`~/.tg-sign.env` takes precedence over `config/public-api.env`. You get your own `api_id` and `api_hash` from Telegram's official API application page: `https://my.telegram.org/apps`.

## iQOO / vivo Background Settings

Do these before expecting stable overnight execution:

- Disable battery optimization for Termux.
- Allow background activity for Termux.
- Allow autostart if the system exposes that option.
- Lock Termux in recent apps.
- In Termux, run `termux-wake-lock` before long scheduler sessions.

Android can still kill background apps. Use `bash scripts/check_status.sh` to inspect state after a night.

## Configure Accounts

```bash
cp config/accounts.example.yaml config/accounts.yaml
```

Edit `config/accounts.yaml`:

```yaml
accounts:
  - name: main
    phone: "+8613800000000"
    session: account_1
  - name: alt1
    phone: "+8613900000000"
    session: account_2
  - name: alt2
    phone: "+8615000000000"
    session: account_3
```

The `session` value controls the local session file name under `data/sessions/`. Do not share or commit session files.

## Configure Tasks

```bash
cp config/tasks.example.yaml config/tasks.yaml
```

Example task that can sign after local midnight:

```yaml
- name: midnight_bot
  bot: "@freexzteam_bot"
  command: "/sign"
  accounts: ["main", "alt1", "alt2"]
  schedule:
    mode: calendar_day
    timezone: Asia/Shanghai
    earliest_time: "00:05"
    random_delay_minutes: [5, 45]
```

Example task that must wait after the last successful sign-in:

```yaml
- name: interval_bot
  bot: "@dw759bot"
  command: "/sign"
  accounts: ["main", "alt1", "alt2"]
  schedule:
    mode: interval_after_success
    min_interval_hours: 24
    random_delay_minutes: [5, 40]
```

## Login

Run:

```bash
bash scripts/login_accounts.sh
```

Pyrogram will create one session per configured account. On first login, Telegram will send code prompts. If you use Telegram two-step verification, enter the password when prompted.

## Dry Run

Before sending Telegram messages:

```bash
python -m src scheduler --accounts config/accounts.yaml --config config/tasks.yaml --state data/state.json --dry-run
```

The output shows `DUE account:task` or `SKIP account:task not-due`.

## Run Scheduler

```bash
termux-wake-lock
bash scripts/run_scheduler.sh
```

The scheduler wrapper loops forever and rechecks every 5 minutes by default. Set `SLEEP_SECONDS` before starting it if you want a different interval. Keep Termux open and exclude it from battery optimization.

## Status

```bash
bash scripts/check_status.sh
```

State is stored in `data/state.json`.

## Telegram Control Bot

Run a separate control bot if you want one-tap control from inside Telegram:

```bash
bash scripts/run_control_bot.sh
```

It needs `CONTROL_BOT_TOKEN` from BotFather, plus `CONTROL_ALLOWED_USER_IDS` or `CONTROL_ALLOWED_USERNAMES`. It still reuses `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.

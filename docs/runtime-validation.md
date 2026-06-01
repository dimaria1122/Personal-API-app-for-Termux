# Runtime Validation

## Current Decision

The first runnable version uses Pyrogram directly instead of embedding TG-SignPulse. TG-SignPulse is still useful as a reference, but it is archived and includes more features than the current phone-first MVP needs.

## Validate Local Runner In Termux

Run in the project directory:

```bash
bash scripts/setup_termux.sh
source ~/.tg-sign.env
python -m src status --state data/state.json
python -m src scheduler --accounts config/accounts.yaml --config config/tasks.yaml --state data/state.json --dry-run
```

Expected:

- Setup installs Python dependencies.
- Status prints `No task state recorded yet.` when no state file exists.
- Dry run prints due or skipped account/task pairs without contacting Telegram.

## Validate Telegram Login

Run:

```bash
source ~/.tg-sign.env
bash scripts/login_accounts.sh
```

Expected:

- Each account prompts for Telegram login only if its session does not already exist.
- Session files are created under `data/sessions/`.
- `LOGGED_IN account_name` prints for each successful account.

## Validate TG-SignPulse Separately

If direct Pyrogram operation is insufficient for a bot with complex button or image flows, validate TG-SignPulse as a secondary backend:

```bash
git clone https://github.com/akasls/TG-SignPulse.git /tmp/TG-SignPulse
cd /tmp/TG-SignPulse
python -m pip install -r requirements.txt
```

Record:

- Whether dependencies install in Termux.
- Whether sessions can be created.
- Whether a simple bot check-in succeeds.
- Whether the flow can be called from this scheduler, or whether the bot should get a dedicated adapter.

from src.credentials import load_api_credentials


def test_load_api_credentials_prefers_environment(monkeypatch):
    monkeypatch.setenv("TELEGRAM_API_ID", "123456")
    monkeypatch.setenv("TELEGRAM_API_HASH", "private_hash")

    credentials = load_api_credentials()

    assert credentials.api_id == 123456
    assert credentials.api_hash == "private_hash"


def test_load_api_credentials_falls_back_to_public_config(monkeypatch, workspace_tmp):
    monkeypatch.delenv("TELEGRAM_API_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_API_HASH", raising=False)
    public_env = workspace_tmp / "public-api.env"
    public_env.write_text(
        "export TELEGRAM_API_ID=2040\n"
        "export TELEGRAM_API_HASH=b18441a1ff607e10a989891a5462e627\n",
        encoding="utf-8",
    )

    credentials = load_api_credentials(public_env)

    assert credentials.api_id == 2040
    assert credentials.api_hash == "b18441a1ff607e10a989891a5462e627"

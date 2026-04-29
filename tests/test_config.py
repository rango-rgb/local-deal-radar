import pytest

from local_deal_radar.config import MissingEbayCredentialsError, load_ebay_config


def disable_dotenv(monkeypatch) -> None:
    monkeypatch.setattr("local_deal_radar.config.load_dotenv", lambda: None)


def test_load_ebay_config_reads_credentials_from_env(monkeypatch) -> None:
    disable_dotenv(monkeypatch)
    monkeypatch.setenv("EBAY_CLIENT_ID", "client-id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("EBAY_MARKETPLACE_ID", "EBAY_GB")
    monkeypatch.setenv("EBAY_ENVIRONMENT", "sandbox")

    config = load_ebay_config()

    assert config.client_id == "client-id"
    assert config.client_secret == "client-secret"
    assert config.marketplace_id == "EBAY_GB"
    assert config.environment == "sandbox"


def test_load_ebay_config_defaults_marketplace_and_environment(monkeypatch) -> None:
    disable_dotenv(monkeypatch)
    monkeypatch.setenv("EBAY_CLIENT_ID", "client-id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "client-secret")
    monkeypatch.delenv("EBAY_MARKETPLACE_ID", raising=False)
    monkeypatch.delenv("EBAY_ENVIRONMENT", raising=False)

    config = load_ebay_config()

    assert config.marketplace_id == "EBAY_US"
    assert config.environment == "production"


def test_missing_client_id_raises_missing_credentials(monkeypatch) -> None:
    disable_dotenv(monkeypatch)
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "client-secret")

    with pytest.raises(MissingEbayCredentialsError):
        load_ebay_config()


def test_missing_client_secret_raises_missing_credentials(monkeypatch) -> None:
    disable_dotenv(monkeypatch)
    monkeypatch.setenv("EBAY_CLIENT_ID", "client-id")
    monkeypatch.delenv("EBAY_CLIENT_SECRET", raising=False)

    with pytest.raises(MissingEbayCredentialsError):
        load_ebay_config()


def test_missing_credentials_error_does_not_include_secrets(monkeypatch) -> None:
    disable_dotenv(monkeypatch)
    monkeypatch.setenv("EBAY_CLIENT_ID", "client-id")
    monkeypatch.delenv("EBAY_CLIENT_SECRET", raising=False)

    with pytest.raises(MissingEbayCredentialsError) as exc_info:
        load_ebay_config()

    message = str(exc_info.value)
    assert "client-id" not in message
    assert "client-secret" not in message

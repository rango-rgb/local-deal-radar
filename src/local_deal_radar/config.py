"""Environment-based configuration for live eBay API access."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class MissingEbayCredentialsError(Exception):
    """Raised when required eBay API credentials are not configured."""


class EbayConfig(BaseModel):
    """Configuration needed for eBay Browse API client credentials flow."""

    client_id: str
    client_secret: str
    marketplace_id: str = "EBAY_US"
    environment: str = Field(default="production")

    @field_validator("client_id", "client_secret", "marketplace_id", "environment")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        value = value.lower()
        if value not in {"production", "sandbox"}:
            raise ValueError("must be either production or sandbox")
        return value


def load_ebay_config() -> EbayConfig:
    """Load eBay credentials from the environment and a local .env file."""

    load_dotenv()
    client_id = _env_value("EBAY_CLIENT_ID")
    client_secret = _env_value("EBAY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise MissingEbayCredentialsError(
            "Missing eBay credentials. Create .env from .env.example and set "
            "EBAY_CLIENT_ID and EBAY_CLIENT_SECRET."
        )

    return EbayConfig(
        client_id=client_id,
        client_secret=client_secret,
        marketplace_id=_env_value("EBAY_MARKETPLACE_ID") or "EBAY_US",
        environment=_env_value("EBAY_ENVIRONMENT") or "production",
    )


def _env_value(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None

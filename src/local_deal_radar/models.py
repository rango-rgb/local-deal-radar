"""Local domain models for deal analysis."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LocalListing(BaseModel):
    """A manually entered local marketplace listing."""

    id: int | None = None
    title: str
    price: float = Field(ge=0)
    category: str
    url: str | None = None
    platform: str | None = None
    location: str | None = None
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("title", "category")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class EbayComp(BaseModel):
    """A comparable eBay listing value entered or fetched in a later step."""

    title: str
    price: float = Field(ge=0)
    shipping: float = Field(default=0, ge=0)
    condition: str | None = None
    url: str | None = None
    source: str | None = "ebay"
    item_id: str | None = None

    @field_validator("title")
    @classmethod
    def require_non_empty_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class DealAnalysis(BaseModel):
    """Conservative local resale analysis output."""

    listing: LocalListing
    comps: list[EbayComp]
    estimated_resale_value: float
    estimated_fees: float
    shipping_cost: float
    transaction_buffer: float
    pickup_cost: float
    risk_buffer: float
    expected_profit: float
    roi: float
    confidence_score: float = Field(ge=0, le=1)
    condition_risk: float = Field(ge=0, le=1)
    scam_risk: float = Field(ge=0, le=1)
    hassle_score: float = Field(ge=0, le=1)
    deal_score: float = Field(ge=0, le=100)
    decision: Literal["pursue", "maybe", "pass"]
    reasons: list[str]
    warnings: list[str]

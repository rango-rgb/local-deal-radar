"""Category profiles used by the conservative scoring engine."""

import re

from pydantic import BaseModel, Field


class CategoryProfile(BaseModel):
    """Conservative category-level resale assumptions."""

    name: str
    ebay_fee_rate: float = Field(ge=0)
    transaction_buffer_rate: float = Field(ge=0)
    default_shipping_cost: float = Field(ge=0)
    default_pickup_cost: float = Field(ge=0)
    risk_buffer_rate: float = Field(ge=0)
    condition_risk: float = Field(ge=0, le=1)
    scam_risk: float = Field(ge=0, le=1)
    hassle_score: float = Field(ge=0, le=1)
    min_comp_count_for_confidence: int = Field(ge=1)


DEFAULT_PROFILE = CategoryProfile(
    name="default",
    ebay_fee_rate=0.1325,
    transaction_buffer_rate=0.02,
    default_shipping_cost=18.0,
    default_pickup_cost=8.0,
    risk_buffer_rate=0.08,
    condition_risk=0.25,
    scam_risk=0.15,
    hassle_score=0.35,
    min_comp_count_for_confidence=4,
)

CATEGORY_PROFILES: dict[str, CategoryProfile] = {
    "cameras": CategoryProfile(
        name="cameras",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=16.0,
        default_pickup_cost=8.0,
        risk_buffer_rate=0.07,
        condition_risk=0.25,
        scam_risk=0.18,
        hassle_score=0.3,
        min_comp_count_for_confidence=4,
    ),
    "lenses": CategoryProfile(
        name="lenses",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=14.0,
        default_pickup_cost=8.0,
        risk_buffer_rate=0.07,
        condition_risk=0.22,
        scam_risk=0.16,
        hassle_score=0.25,
        min_comp_count_for_confidence=4,
    ),
    "vintage_audio": CategoryProfile(
        name="vintage_audio",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=45.0,
        default_pickup_cost=12.0,
        risk_buffer_rate=0.12,
        condition_risk=0.45,
        scam_risk=0.18,
        hassle_score=0.65,
        min_comp_count_for_confidence=4,
    ),
    "bikes": CategoryProfile(
        name="bikes",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=95.0,
        default_pickup_cost=15.0,
        risk_buffer_rate=0.1,
        condition_risk=0.35,
        scam_risk=0.16,
        hassle_score=0.75,
        min_comp_count_for_confidence=4,
    ),
    "bike_parts": CategoryProfile(
        name="bike_parts",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=18.0,
        default_pickup_cost=8.0,
        risk_buffer_rate=0.08,
        condition_risk=0.28,
        scam_risk=0.12,
        hassle_score=0.35,
        min_comp_count_for_confidence=4,
    ),
    "outdoor_gear": CategoryProfile(
        name="outdoor_gear",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=28.0,
        default_pickup_cost=10.0,
        risk_buffer_rate=0.09,
        condition_risk=0.3,
        scam_risk=0.12,
        hassle_score=0.45,
        min_comp_count_for_confidence=4,
    ),
    "tools": CategoryProfile(
        name="tools",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=25.0,
        default_pickup_cost=10.0,
        risk_buffer_rate=0.08,
        condition_risk=0.25,
        scam_risk=0.14,
        hassle_score=0.45,
        min_comp_count_for_confidence=4,
    ),
    "electronics": CategoryProfile(
        name="electronics",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=20.0,
        default_pickup_cost=8.0,
        risk_buffer_rate=0.1,
        condition_risk=0.38,
        scam_risk=0.22,
        hassle_score=0.45,
        min_comp_count_for_confidence=4,
    ),
    "video_games": CategoryProfile(
        name="video_games",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=7.0,
        default_pickup_cost=6.0,
        risk_buffer_rate=0.06,
        condition_risk=0.18,
        scam_risk=0.12,
        hassle_score=0.2,
        min_comp_count_for_confidence=5,
    ),
    "collectibles": CategoryProfile(
        name="collectibles",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=12.0,
        default_pickup_cost=6.0,
        risk_buffer_rate=0.12,
        condition_risk=0.35,
        scam_risk=0.2,
        hassle_score=0.4,
        min_comp_count_for_confidence=5,
    ),
    "musical_instruments": CategoryProfile(
        name="musical_instruments",
        ebay_fee_rate=0.1325,
        transaction_buffer_rate=0.02,
        default_shipping_cost=40.0,
        default_pickup_cost=12.0,
        risk_buffer_rate=0.1,
        condition_risk=0.32,
        scam_risk=0.16,
        hassle_score=0.55,
        min_comp_count_for_confidence=4,
    ),
    "default": DEFAULT_PROFILE,
}


def normalize_category(category: str) -> str:
    """Normalize display category text to a snake_case lookup key."""

    normalized = re.sub(r"[^a-z0-9]+", "_", category.strip().lower())
    return normalized.strip("_")


def get_category_profile(category: str) -> CategoryProfile:
    """Return a category profile, falling back to the conservative default."""

    return CATEGORY_PROFILES.get(normalize_category(category), DEFAULT_PROFILE)

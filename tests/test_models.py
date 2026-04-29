from datetime import datetime

import pytest
from pydantic import ValidationError

from local_deal_radar.models import DealAnalysis, EbayComp, LocalListing


def make_listing() -> LocalListing:
    return LocalListing(title="Canon camera", price=100, category="cameras")


def make_comp() -> EbayComp:
    return EbayComp(title="Canon camera sold listing", price=180, shipping=12)


def test_local_listing_valid_creation() -> None:
    listing = make_listing()

    assert listing.id is None
    assert listing.title == "Canon camera"
    assert listing.price == 100
    assert listing.category == "cameras"
    assert isinstance(listing.created_at, datetime)


def test_local_listing_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        LocalListing(title=" ", price=100, category="cameras")


def test_local_listing_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        LocalListing(title="Canon camera", price=-1, category="cameras")


def test_ebay_comp_valid_creation() -> None:
    comp = make_comp()

    assert comp.title == "Canon camera sold listing"
    assert comp.price == 180
    assert comp.shipping == 12
    assert comp.source == "ebay"


def test_ebay_comp_rejects_negative_price_or_shipping() -> None:
    with pytest.raises(ValidationError):
        EbayComp(title="Bad comp", price=-1)

    with pytest.raises(ValidationError):
        EbayComp(title="Bad comp", price=10, shipping=-1)


def test_deal_analysis_accepts_valid_decision() -> None:
    analysis = DealAnalysis(
        listing=make_listing(),
        comps=[make_comp()],
        estimated_resale_value=192,
        estimated_fees=25.44,
        shipping_cost=16,
        transaction_buffer=3.84,
        pickup_cost=8,
        risk_buffer=13.44,
        expected_profit=25.28,
        roi=0.2528,
        confidence_score=0.5,
        condition_risk=0.25,
        scam_risk=0.18,
        hassle_score=0.3,
        deal_score=42,
        decision="maybe",
        reasons=["Expected profit is plausible."],
        warnings=["Active eBay comps are not sold comps and require manual verification."],
    )

    assert analysis.decision == "maybe"


def test_deal_analysis_rejects_invalid_decision() -> None:
    with pytest.raises(ValidationError):
        DealAnalysis(
            listing=make_listing(),
            comps=[make_comp()],
            estimated_resale_value=192,
            estimated_fees=25.44,
            shipping_cost=16,
            transaction_buffer=3.84,
            pickup_cost=8,
            risk_buffer=13.44,
            expected_profit=25.28,
            roi=0.2528,
            confidence_score=0.5,
            condition_risk=0.25,
            scam_risk=0.18,
            hassle_score=0.3,
            deal_score=42,
            decision="buy",
            reasons=[],
            warnings=[],
        )

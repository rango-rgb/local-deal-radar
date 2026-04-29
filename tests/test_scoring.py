import pytest

from local_deal_radar.scoring import ACTIVE_COMPS_WARNING, analyze_deal
from local_deal_radar.models import EbayComp, LocalListing


def listing(price: float = 100, category: str = "cameras", title: str = "Canon camera") -> LocalListing:
    return LocalListing(title=title, price=price, category=category)


def comps(values: list[float]) -> list[EbayComp]:
    return [EbayComp(title=f"Comp {index}", price=value) for index, value in enumerate(values)]


def test_no_comps_returns_pass_with_low_confidence_and_warning() -> None:
    analysis = analyze_deal(listing(), [])

    assert analysis.decision == "pass"
    assert analysis.estimated_resale_value == 0
    assert analysis.expected_profit < 0
    assert analysis.confidence_score == 0
    assert any("No comps were provided" in warning for warning in analysis.warnings)


def test_fee_and_profit_math_is_approximately_correct() -> None:
    analysis = analyze_deal(
        listing(price=50, category="video_games", title="Nintendo bundle"),
        comps([120, 120, 120, 120, 120]),
    )

    assert analysis.estimated_resale_value == 120
    assert analysis.estimated_fees == pytest.approx(15.9)
    assert analysis.transaction_buffer == pytest.approx(2.4)
    assert analysis.shipping_cost == pytest.approx(7)
    assert analysis.pickup_cost == pytest.approx(6)
    assert analysis.risk_buffer == pytest.approx(7.2)
    assert analysis.expected_profit == pytest.approx(31.5)


def test_roi_math_is_correct() -> None:
    analysis = analyze_deal(
        listing(price=50, category="video_games", title="Nintendo bundle"),
        comps([120, 120, 120, 120, 120]),
    )

    assert analysis.roi == pytest.approx(0.63)


def test_pursue_threshold_works() -> None:
    analysis = analyze_deal(listing(price=100), comps([250, 250, 250, 250]))

    assert analysis.decision == "pursue"


def test_maybe_threshold_works() -> None:
    analysis = analyze_deal(
        listing(price=50, category="video_games", title="Nintendo bundle"),
        comps([120, 120, 120, 120, 120]),
    )

    assert analysis.decision == "maybe"


def test_pass_threshold_works() -> None:
    analysis = analyze_deal(
        listing(price=100, category="video_games", title="Nintendo bundle"),
        comps([130, 130, 130, 130, 130]),
    )

    assert analysis.decision == "pass"


def test_low_comp_count_lowers_confidence() -> None:
    analysis = analyze_deal(listing(), comps([250]))

    assert analysis.confidence_score < 0.45
    assert any("Low comp count" in warning for warning in analysis.warnings)


def test_wide_comp_spread_lowers_confidence() -> None:
    analysis = analyze_deal(listing(), comps([100, 105, 500, 900]))

    assert analysis.confidence_score < 0.45
    assert any("Wide comp spread" in warning for warning in analysis.warnings)


def test_active_comps_warning_is_always_present() -> None:
    no_comp_analysis = analyze_deal(listing(), [])
    comp_analysis = analyze_deal(listing(), comps([250, 250, 250, 250]))

    assert ACTIVE_COMPS_WARNING in no_comp_analysis.warnings
    assert ACTIVE_COMPS_WARNING in comp_analysis.warnings


def test_condition_risk_keywords_increase_condition_risk_and_add_warning() -> None:
    clean = analyze_deal(listing(), comps([250, 250, 250, 250]))
    risky_listing = LocalListing(
        title="Canon camera for parts",
        price=100,
        category="cameras",
        description="Untested, as is, missing charger.",
    )
    risky = analyze_deal(risky_listing, comps([250, 250, 250, 250]))

    assert risky.condition_risk > clean.condition_risk
    assert any("Condition-risk keywords" in warning for warning in risky.warnings)


def test_valuation_uses_trimmed_median_not_max_comp() -> None:
    analysis = analyze_deal(listing(), comps([100, 110, 120, 130, 1000]))

    assert analysis.estimated_resale_value == 120
    assert analysis.estimated_resale_value != 1000

"""Conservative local deal scoring."""

from statistics import median

from local_deal_radar.categories import get_category_profile
from local_deal_radar.models import DealAnalysis, EbayComp, LocalListing

ACTIVE_COMPS_WARNING = (
    "Active eBay comps are not sold comps and require manual verification."
)
CONDITION_KEYWORDS = ("broken", "for parts", "untested", "as is", "repair", "missing")
SCAM_KEYWORDS = ("wire", "deposit", "cashapp", "zelle only", "ship only")


def analyze_deal(listing: LocalListing, comps: list[EbayComp]) -> DealAnalysis:
    """Analyze a local listing against supplied comps with conservative math."""

    profile = get_category_profile(listing.category)
    warnings = [ACTIVE_COMPS_WARNING]
    reasons: list[str] = []

    condition_risk, condition_warnings = _condition_risk(listing, profile.condition_risk)
    warnings.extend(condition_warnings)
    scam_risk = _scam_risk(listing, profile.scam_risk)
    hassle_score = profile.hassle_score

    if not comps:
        warnings.append("No comps were provided; valuation confidence is low.")
        estimated_resale_value = 0.0
        estimated_fees = 0.0
        transaction_buffer = 0.0
        shipping_cost = profile.default_shipping_cost
        pickup_cost = profile.default_pickup_cost
        risk_buffer = 0.0
        expected_profit = (
            estimated_resale_value
            - listing.price
            - estimated_fees
            - transaction_buffer
            - shipping_cost
            - pickup_cost
            - risk_buffer
        )
        roi = _roi(expected_profit, listing.price)
        reasons.append("No comparable listings were available, so the deal is a pass.")
        return DealAnalysis(
            listing=listing,
            comps=comps,
            estimated_resale_value=estimated_resale_value,
            estimated_fees=estimated_fees,
            shipping_cost=shipping_cost,
            transaction_buffer=transaction_buffer,
            pickup_cost=pickup_cost,
            risk_buffer=risk_buffer,
            expected_profit=expected_profit,
            roi=roi,
            confidence_score=0.0,
            condition_risk=condition_risk,
            scam_risk=scam_risk,
            hassle_score=hassle_score,
            deal_score=0.0,
            decision="pass",
            reasons=reasons,
            warnings=warnings,
        )

    comp_values = [comp.price + comp.shipping for comp in comps]
    estimated_resale_value = _conservative_comp_value(comp_values)
    estimated_fees = estimated_resale_value * profile.ebay_fee_rate
    transaction_buffer = estimated_resale_value * profile.transaction_buffer_rate
    shipping_cost = profile.default_shipping_cost
    pickup_cost = profile.default_pickup_cost
    risk_buffer = estimated_resale_value * profile.risk_buffer_rate
    expected_profit = (
        estimated_resale_value
        - listing.price
        - estimated_fees
        - transaction_buffer
        - shipping_cost
        - pickup_cost
        - risk_buffer
    )
    roi = _roi(expected_profit, listing.price)
    confidence_score, confidence_warnings = _confidence_score(
        comp_values,
        estimated_resale_value,
        profile.min_comp_count_for_confidence,
    )
    warnings.extend(confidence_warnings)
    decision = _decision(expected_profit, roi, confidence_score)
    deal_score = _deal_score(expected_profit, roi, confidence_score, condition_risk, scam_risk)
    reasons.extend(_decision_reasons(decision, expected_profit, roi, confidence_score))

    return DealAnalysis(
        listing=listing,
        comps=comps,
        estimated_resale_value=estimated_resale_value,
        estimated_fees=estimated_fees,
        shipping_cost=shipping_cost,
        transaction_buffer=transaction_buffer,
        pickup_cost=pickup_cost,
        risk_buffer=risk_buffer,
        expected_profit=expected_profit,
        roi=roi,
        confidence_score=confidence_score,
        condition_risk=condition_risk,
        scam_risk=scam_risk,
        hassle_score=hassle_score,
        deal_score=deal_score,
        decision=decision,
        reasons=reasons,
        warnings=warnings,
    )


def _conservative_comp_value(values: list[float]) -> float:
    sorted_values = sorted(values)
    if len(sorted_values) >= 5:
        trim_count = max(1, int(len(sorted_values) * 0.1))
        sorted_values = sorted_values[trim_count:-trim_count]
    return float(median(sorted_values))


def _confidence_score(
    values: list[float],
    estimated_resale_value: float,
    min_comp_count: int,
) -> tuple[float, list[str]]:
    warnings: list[str] = []
    count_factor = min(1.0, len(values) / min_comp_count)
    if len(values) < min_comp_count:
        warnings.append("Low comp count; valuation confidence is reduced.")

    if estimated_resale_value <= 0:
        return 0.0, warnings

    spread_ratio = (max(values) - min(values)) / estimated_resale_value
    if spread_ratio >= 0.6:
        warnings.append("Wide comp spread; valuation confidence is reduced.")

    spread_factor = max(0.25, 1 - (spread_ratio * 0.5))
    confidence = count_factor * spread_factor
    return round(max(0.0, min(1.0, confidence)), 2), warnings


def _condition_risk(listing: LocalListing, baseline: float) -> tuple[float, list[str]]:
    text = f"{listing.title} {listing.description or ''}".lower()
    matched = [keyword for keyword in CONDITION_KEYWORDS if keyword in text]
    if not matched:
        return baseline, []

    warning = (
        "Condition-risk keywords found: "
        + ", ".join(matched)
        + "; manual inspection is required."
    )
    return min(1.0, baseline + 0.2), [warning]


def _scam_risk(listing: LocalListing, baseline: float) -> float:
    text = f"{listing.title} {listing.description or ''}".lower()
    if any(keyword in text for keyword in SCAM_KEYWORDS):
        return min(1.0, baseline + 0.1)
    return baseline


def _decision(expected_profit: float, roi: float, confidence_score: float) -> str:
    if expected_profit >= 50 and roi >= 0.40 and confidence_score >= 0.65:
        return "pursue"
    if expected_profit >= 30 and roi >= 0.25 and confidence_score >= 0.45:
        return "maybe"
    return "pass"


def _decision_reasons(
    decision: str,
    expected_profit: float,
    roi: float,
    confidence_score: float,
) -> list[str]:
    if decision == "pursue":
        return [
            "Expected profit, ROI, and confidence meet pursue thresholds.",
            f"Expected profit is ${expected_profit:.2f} with ROI {roi:.2%}.",
        ]
    if decision == "maybe":
        return [
            "Expected profit, ROI, and confidence meet maybe thresholds but not pursue thresholds.",
            f"Expected profit is ${expected_profit:.2f} with ROI {roi:.2%}.",
        ]
    return [
        "Expected profit, ROI, or confidence did not meet maybe thresholds.",
        f"Expected profit is ${expected_profit:.2f} with ROI {roi:.2%}.",
    ]


def _deal_score(
    expected_profit: float,
    roi: float,
    confidence_score: float,
    condition_risk: float,
    scam_risk: float,
) -> float:
    profit_component = min(40.0, max(0.0, expected_profit) / 2.5)
    roi_component = min(30.0, max(0.0, roi) * 60)
    confidence_component = confidence_score * 30
    risk_penalty = (condition_risk + scam_risk) * 10
    return round(max(0.0, min(100.0, profit_component + roi_component + confidence_component - risk_penalty)), 2)


def _roi(expected_profit: float, listing_price: float) -> float:
    if listing_price <= 0:
        return 0.0
    return expected_profit / listing_price

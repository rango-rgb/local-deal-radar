from local_deal_radar.models import DealAnalysis, EbayComp, LocalListing
from local_deal_radar.reporting import rank_opportunities, report_to_dict


def make_analysis(
    decision: str,
    deal_score: float,
    expected_profit: float,
    listing_id: int,
    title: str,
) -> DealAnalysis:
    listing = LocalListing(
        id=listing_id,
        title=title,
        price=100,
        category="cameras",
        platform="facebook",
        location="Portland, OR",
    )
    return DealAnalysis(
        listing=listing,
        comps=[EbayComp(title=f"{title} comp", price=200, shipping=10)],
        estimated_resale_value=210,
        estimated_fees=27.83,
        shipping_cost=16,
        transaction_buffer=4.2,
        pickup_cost=8,
        risk_buffer=14.7,
        expected_profit=expected_profit,
        roi=expected_profit / listing.price,
        confidence_score=0.8,
        condition_risk=0.25,
        scam_risk=0.18,
        hassle_score=0.3,
        deal_score=deal_score,
        decision=decision,
        reasons=[f"{decision} reason"],
        warnings=["Active eBay comps are not sold comps and require manual verification."],
    )


def test_report_ranking_prioritizes_pursue_above_maybe_above_pass() -> None:
    analyses = [
        make_analysis("pass", 99, 500, 1, "Pass listing"),
        make_analysis("maybe", 50, 40, 2, "Maybe listing"),
        make_analysis("pursue", 10, 20, 3, "Pursue listing"),
    ]

    ranked = rank_opportunities(analyses)

    assert [analysis.decision for analysis in ranked] == ["pursue", "maybe", "pass"]


def test_report_ranking_uses_deal_score_and_profit_within_decision_class() -> None:
    analyses = [
        make_analysis("maybe", 60, 100, 1, "Lower score"),
        make_analysis("maybe", 80, 50, 2, "Higher score"),
        make_analysis("maybe", 80, 90, 3, "Higher profit"),
    ]

    ranked = rank_opportunities(analyses)

    assert [analysis.listing.title for analysis in ranked] == [
        "Higher profit",
        "Higher score",
        "Lower score",
    ]


def test_report_ranking_respects_limit() -> None:
    analyses = [
        make_analysis("maybe", 80, 80, 1, "First"),
        make_analysis("maybe", 70, 70, 2, "Second"),
    ]

    ranked = rank_opportunities(analyses, limit=1)

    assert len(ranked) == 1
    assert ranked[0].listing.title == "First"


def test_report_json_serialization_includes_required_fields() -> None:
    payload = report_to_dict(
        [make_analysis("maybe", 70, 50, 42, "Sony a6000 camera body")]
    )
    opportunity = payload["opportunities"][0]

    assert payload["count"] == 1
    assert {
        "listing_id",
        "title",
        "price",
        "category",
        "platform",
        "location",
        "estimated_resale_value",
        "expected_profit",
        "roi",
        "confidence_score",
        "deal_score",
        "decision",
        "reasons",
        "warnings",
        "comp_count",
    } <= opportunity.keys()


def test_empty_report_serializes_empty_structure() -> None:
    payload = report_to_dict([])

    assert payload == {"count": 0, "opportunities": []}


def test_report_filters_by_decision_and_min_profit() -> None:
    analyses = [
        make_analysis("maybe", 80, 20, 1, "Too low"),
        make_analysis("maybe", 70, 60, 2, "Keep"),
        make_analysis("pursue", 90, 100, 3, "Wrong decision"),
    ]

    ranked = rank_opportunities(analyses, decision="maybe", min_profit=50)

    assert [analysis.listing.title for analysis in ranked] == ["Keep"]

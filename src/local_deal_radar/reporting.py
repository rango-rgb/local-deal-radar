"""Display helpers for deal analysis and comps output."""

from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from local_deal_radar.models import DealAnalysis, EbayComp, LocalListing

ACTIVE_COMPS_REPORT_WARNING = (
    "Active eBay comps are not sold comps; manually verify before buying."
)
DECISION_PRIORITY = {"pursue": 0, "maybe": 1, "pass": 2}


def analysis_to_dict(
    analysis: DealAnalysis,
    analysis_id: int | None = None,
    listing_id: int | None = None,
) -> dict:
    """Convert an analysis to JSON-serializable built-in types."""

    payload = analysis.model_dump(mode="json")
    if listing_id is not None:
        payload["listing_id"] = listing_id
    if analysis_id is not None:
        payload["analysis_id"] = analysis_id
    return payload


def comps_to_dicts(comps: list[EbayComp]) -> list[dict]:
    """Convert comps to JSON-serializable built-in types."""

    return [comp.model_dump(mode="json") for comp in comps]


def listings_to_dicts(listings: list[LocalListing]) -> list[dict]:
    """Convert listings to JSON-serializable built-in types."""

    return [listing.model_dump(mode="json") for listing in listings]


def rank_opportunities(
    analyses: list[DealAnalysis],
    limit: int = 10,
    decision: str | None = None,
    min_profit: float | None = None,
) -> list[DealAnalysis]:
    """Filter and rank saved analyses for the v0 report."""

    filtered = analyses
    if decision is not None:
        filtered = [analysis for analysis in filtered if analysis.decision == decision]
    if min_profit is not None:
        filtered = [
            analysis
            for analysis in filtered
            if analysis.expected_profit >= min_profit
        ]

    ranked = sorted(
        filtered,
        key=lambda analysis: (
            DECISION_PRIORITY[analysis.decision],
            -analysis.deal_score,
            -analysis.expected_profit,
        ),
    )
    return ranked[: max(1, int(limit))]


def report_to_dict(opportunities: list[DealAnalysis]) -> dict:
    """Convert ranked report opportunities to JSON-serializable data."""

    return {
        "count": len(opportunities),
        "opportunities": [
            {
                "listing_id": analysis.listing.id,
                "title": analysis.listing.title,
                "price": analysis.listing.price,
                "category": analysis.listing.category,
                "platform": analysis.listing.platform,
                "location": analysis.listing.location,
                "estimated_resale_value": analysis.estimated_resale_value,
                "expected_profit": analysis.expected_profit,
                "roi": analysis.roi,
                "confidence_score": analysis.confidence_score,
                "deal_score": analysis.deal_score,
                "decision": analysis.decision,
                "reasons": analysis.reasons,
                "warnings": analysis.warnings,
                "comp_count": len(analysis.comps),
            }
            for analysis in opportunities
        ],
    }


def render_analysis(
    analysis: DealAnalysis,
    analysis_id: int | None = None,
    listing_id: int | None = None,
) -> Panel:
    """Build a Rich renderable for a deal analysis."""

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("Decision", analysis.decision.upper())
    summary.add_row("Expected profit", f"${analysis.expected_profit:.2f}")
    summary.add_row("ROI", f"{analysis.roi:.2%}")
    summary.add_row("Estimated resale", f"${analysis.estimated_resale_value:.2f}")
    summary.add_row("Confidence", f"{analysis.confidence_score:.2f}")
    summary.add_row("Deal score", f"{analysis.deal_score:.2f}")
    if listing_id is not None:
        summary.add_row("Saved listing id", str(listing_id))
    if analysis_id is not None:
        summary.add_row("Saved analysis id", str(analysis_id))

    comps = render_comps_table(analysis.comps)
    comps.title = "eBay Active Comps"

    reasons = Table.grid()
    reasons.add_column()
    for reason in analysis.reasons:
        reasons.add_row(f"- {reason}")

    warnings = Table.grid()
    warnings.add_column()
    for warning in analysis.warnings:
        warnings.add_row(f"- {warning}")

    return Panel(
        Group(summary, comps, "Reasons", reasons, "Warnings", warnings),
        title=f"{analysis.listing.title} (${analysis.listing.price:.2f})",
    )


def render_comps_table(comps: list[EbayComp]) -> Table:
    """Build a Rich table for comparable listings."""

    table = Table(title="eBay Active Comps", show_lines=False)
    table.add_column("Title")
    table.add_column("Price", justify="right")
    table.add_column("Shipping", justify="right")
    table.add_column("Condition")
    table.add_column("Source")
    for comp in comps:
        table.add_row(
            comp.title,
            f"${comp.price:.2f}",
            f"${comp.shipping:.2f}",
            comp.condition or "",
            comp.source or "",
        )

    return table


def render_listings_table(listings: list[LocalListing]) -> Table:
    """Build a Rich table for saved listings."""

    table = Table(title="Saved Listings", show_lines=False)
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Price", justify="right")
    table.add_column("Category")
    table.add_column("Platform")
    table.add_column("Location")
    for listing in listings:
        table.add_row(
            str(listing.id or ""),
            listing.title,
            f"${listing.price:.2f}",
            listing.category,
            listing.platform or "",
            listing.location or "",
        )

    return table


def render_report(opportunities: list[DealAnalysis]) -> Panel:
    """Build a Rich report table for ranked saved analyses."""

    table = Table(title="Saved Opportunity Report", show_lines=False)
    table.add_column("Rank", justify="right")
    table.add_column("Listing ID", justify="right")
    table.add_column("Title")
    table.add_column("Decision")
    table.add_column("Expected Profit", justify="right")
    table.add_column("ROI", justify="right")
    table.add_column("Confidence", justify="right")
    table.add_column("Deal Score", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Estimated Resale", justify="right")
    table.add_column("Platform")
    table.add_column("Location")

    for rank, analysis in enumerate(opportunities, start=1):
        listing = analysis.listing
        table.add_row(
            str(rank),
            str(listing.id or ""),
            listing.title,
            analysis.decision.upper(),
            f"${analysis.expected_profit:.2f}",
            f"{analysis.roi:.2%}",
            f"{analysis.confidence_score:.2f}",
            f"{analysis.deal_score:.2f}",
            f"${listing.price:.2f}",
            f"${analysis.estimated_resale_value:.2f}",
            listing.platform or "",
            listing.location or "",
        )

    return Panel(Group(table, ACTIVE_COMPS_REPORT_WARNING), title="Local Deal Radar")

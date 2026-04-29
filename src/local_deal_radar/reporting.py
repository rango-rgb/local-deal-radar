"""Display helpers for deal analysis and comps output."""

from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from local_deal_radar.models import DealAnalysis, EbayComp


def analysis_to_dict(analysis: DealAnalysis) -> dict:
    """Convert an analysis to JSON-serializable built-in types."""

    return analysis.model_dump(mode="json")


def comps_to_dicts(comps: list[EbayComp]) -> list[dict]:
    """Convert comps to JSON-serializable built-in types."""

    return [comp.model_dump(mode="json") for comp in comps]


def render_analysis(analysis: DealAnalysis) -> Panel:
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

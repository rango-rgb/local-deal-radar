"""Typer CLI entrypoint for Local Deal Radar."""

import json
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console

from local_deal_radar import __version__
from local_deal_radar.ebay import MockEbayClient
from local_deal_radar.models import LocalListing
from local_deal_radar.reporting import analysis_to_dict, render_analysis
from local_deal_radar.scoring import analyze_deal

app = typer.Typer(
    help="Local-first resale intelligence CLI for manually entered listings.",
    no_args_is_help=True,
)
listings_app = typer.Typer(help="Manage saved listings.", no_args_is_help=True)


@app.command()
def version() -> None:
    """Show the installed Local Deal Radar version."""
    typer.echo(f"local-deal-radar {__version__}")


@app.command()
def analyze(
    title: Annotated[str | None, typer.Option("--title", help="Manual listing title.")] = None,
    price: Annotated[float | None, typer.Option("--price", min=0, help="Manual listing price.")] = None,
    category: Annotated[str | None, typer.Option("--category", help="Listing category.")] = None,
    platform: Annotated[str | None, typer.Option("--platform", help="Source marketplace.")] = None,
    location: Annotated[str | None, typer.Option("--location", help="Listing location.")] = None,
    url: Annotated[str | None, typer.Option("--url", help="Listing URL.")] = None,
    description: Annotated[str | None, typer.Option("--description", help="Listing notes.")] = None,
    mock: Annotated[bool, typer.Option("--mock", help="Use deterministic offline eBay mock comps.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Print parseable JSON only.")] = False,
) -> None:
    """Analyze a manually entered listing."""
    if not mock:
        typer.echo(
            "Live eBay analysis is not implemented yet. Use --mock for offline mock analysis. "
            "Analyze command is not implemented yet."
        )
        return

    _require_mock_option(title, "--title")
    _require_mock_option(price, "--price")
    _require_mock_option(category, "--category")

    try:
        listing = LocalListing(
            title=title,
            price=price,
            category=category,
            platform=platform,
            location=location,
            url=url,
            description=description,
        )
    except ValidationError as exc:
        raise typer.BadParameter(str(exc)) from exc
    comps = MockEbayClient().search_comps(title, category=category)
    analysis = analyze_deal(listing, comps)

    if json_output:
        typer.echo(json.dumps(analysis_to_dict(analysis), indent=2))
        return

    Console().print(render_analysis(analysis))


@app.command()
def comps() -> None:
    """Fetch comparable sales for a listing."""
    typer.echo("Comps command is not implemented yet.")


@listings_app.command("add")
def listings_add() -> None:
    """Add a saved listing."""
    typer.echo("Saved listings are not implemented yet.")


@listings_app.command("list")
def listings_list() -> None:
    """List saved listings."""
    typer.echo("Saved listings are not implemented yet.")


@app.command()
def analyze_saved(listing_id: str) -> None:
    """Analyze a saved listing by ID."""
    typer.echo("Saved listings are not implemented yet.")


@app.command()
def report() -> None:
    """Generate a report."""
    typer.echo("Report command is not implemented yet.")


app.add_typer(listings_app, name="listings")


def _require_mock_option(value: object, option_name: str) -> None:
    if value is None:
        raise typer.BadParameter(
            f"{option_name} is required when using --mock.",
            param_hint=option_name,
        )

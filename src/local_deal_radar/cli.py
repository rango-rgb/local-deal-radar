"""Typer CLI entrypoint for Local Deal Radar."""

import json
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console

from local_deal_radar import __version__
from local_deal_radar.config import MissingEbayCredentialsError
from local_deal_radar.ebay import EbayApiError, EbayBrowseClient, MockEbayClient
from local_deal_radar.models import EbayComp, LocalListing
from local_deal_radar.reporting import (
    analysis_to_dict,
    comps_to_dicts,
    render_analysis,
    render_comps_table,
)
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
    _require_option(title, "--title")
    _require_option(price, "--price")
    _require_option(category, "--category")

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

    client = MockEbayClient() if mock else EbayBrowseClient()
    comps = _search_comps_or_exit(client, title, category=category)
    analysis = analyze_deal(listing, comps)

    if json_output:
        typer.echo(json.dumps(analysis_to_dict(analysis), indent=2))
        return

    Console().print(render_analysis(analysis))


@app.command()
def comps(
    query: Annotated[str, typer.Option("--query", help="Search query.")],
    category: Annotated[str | None, typer.Option("--category", help="Local category.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum comps to return.")] = 10,
    mock: Annotated[bool, typer.Option("--mock", help="Use deterministic offline eBay mock comps.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Print parseable JSON only.")] = False,
) -> None:
    """Fetch comparable sales for a listing."""
    client = MockEbayClient() if mock else EbayBrowseClient()
    found_comps = _search_comps_or_exit(client, query, category=category, limit=limit)

    if json_output:
        typer.echo(json.dumps(comps_to_dicts(found_comps), indent=2))
        return

    Console().print(render_comps_table(found_comps))


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


def _require_option(value: object, option_name: str) -> None:
    if value is None:
        raise typer.BadParameter(
            f"{option_name} is required.",
            param_hint=option_name,
        )


def _search_comps_or_exit(
    client: MockEbayClient | EbayBrowseClient,
    query: str,
    category: str | None = None,
    limit: int = 10,
) -> list[EbayComp]:
    try:
        return client.search_comps(query, category=category, limit=limit)
    except MissingEbayCredentialsError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    except EbayApiError as exc:
        typer.echo(f"eBay API error: {exc}")
        raise typer.Exit(code=1) from exc

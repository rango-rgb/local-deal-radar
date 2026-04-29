"""Typer CLI entrypoint for Local Deal Radar."""

import json
from pathlib import Path
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
    render_listings_table,
    listings_to_dicts,
)
from local_deal_radar.scoring import analyze_deal
from local_deal_radar.storage import DEFAULT_DB_PATH, DealStore

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
    save: Annotated[bool, typer.Option("--save", help="Save listing, analysis, and comps.")] = False,
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
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
    saved_listing_id: int | None = None
    saved_analysis_id: int | None = None

    if save:
        store = DealStore(db_path)
        saved_listing = store.save_listing(listing)
        analysis = analysis.model_copy(update={"listing": saved_listing})
        saved_listing_id = saved_listing.id
        saved_analysis_id = store.save_analysis(analysis)

    if json_output:
        typer.echo(
            json.dumps(
                analysis_to_dict(
                    analysis,
                    analysis_id=saved_analysis_id,
                    listing_id=saved_listing_id,
                ),
                indent=2,
            )
        )
        return

    Console().print(
        render_analysis(
            analysis,
            analysis_id=saved_analysis_id,
            listing_id=saved_listing_id,
        )
    )


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
def listings_add(
    title: Annotated[str, typer.Option("--title", help="Manual listing title.")],
    price: Annotated[float, typer.Option("--price", min=0, help="Manual listing price.")],
    category: Annotated[str, typer.Option("--category", help="Listing category.")],
    platform: Annotated[str | None, typer.Option("--platform", help="Source marketplace.")] = None,
    location: Annotated[str | None, typer.Option("--location", help="Listing location.")] = None,
    url: Annotated[str | None, typer.Option("--url", help="Listing URL.")] = None,
    description: Annotated[str | None, typer.Option("--description", help="Listing notes.")] = None,
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
) -> None:
    """Add a saved listing."""
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

    saved_listing = DealStore(db_path).save_listing(listing)
    typer.echo(f"Saved listing {saved_listing.id}: {saved_listing.title}")


@listings_app.command("list")
def listings_list(
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum listings to show.")] = 50,
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
    json_output: Annotated[bool, typer.Option("--json", help="Print parseable JSON only.")] = False,
) -> None:
    """List saved listings."""
    listings = DealStore(db_path).list_listings(limit=limit)

    if json_output:
        typer.echo(json.dumps(listings_to_dicts(listings), indent=2))
        return

    if not listings:
        typer.echo("No saved listings yet.")
        return

    Console().print(render_listings_table(listings))


@app.command()
def analyze_saved(
    listing_id: int,
    mock: Annotated[bool, typer.Option("--mock", help="Use deterministic offline eBay mock comps.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Print parseable JSON only.")] = False,
    db_path: Annotated[Path, typer.Option("--db-path", help="SQLite database path.")] = DEFAULT_DB_PATH,
) -> None:
    """Analyze a saved listing by ID."""
    store = DealStore(db_path)
    listing = store.get_listing(listing_id)
    if listing is None:
        typer.echo(f"Saved listing {listing_id} was not found.")
        raise typer.Exit(code=1)

    client = MockEbayClient() if mock else EbayBrowseClient()
    comps = _search_comps_or_exit(client, listing.title, category=listing.category)
    analysis = analyze_deal(listing, comps)
    analysis_id = store.save_analysis(analysis)

    if json_output:
        typer.echo(
            json.dumps(
                analysis_to_dict(
                    analysis,
                    analysis_id=analysis_id,
                    listing_id=listing.id,
                ),
                indent=2,
            )
        )
        return

    Console().print(
        render_analysis(
            analysis,
            analysis_id=analysis_id,
            listing_id=listing.id,
        )
    )


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

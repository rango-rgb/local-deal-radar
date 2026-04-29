"""Typer CLI entrypoint for Local Deal Radar."""

import typer

from local_deal_radar import __version__

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
def analyze() -> None:
    """Analyze a manually entered listing."""
    typer.echo("Analyze command is not implemented yet.")


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

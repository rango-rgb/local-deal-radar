import shutil
import uuid
from pathlib import Path

import pytest
from typer.testing import CliRunner

from local_deal_radar.cli import app

runner = CliRunner()


@pytest.fixture
def db_path() -> Path:
    base = Path(".test-data") / f"cli-core-{uuid.uuid4().hex}"
    try:
        yield base / "deals.sqlite3"
    finally:
        if base.exists():
            shutil.rmtree(base)


def test_cli_help_works() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Local-first resale intelligence CLI" in result.output


def test_version_command_works() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "local-deal-radar 0.1.0" in result.output


def test_analyze_help_works() -> None:
    result = runner.invoke(app, ["analyze", "--help"])

    assert result.exit_code == 0
    assert "Analyze a manually entered listing." in result.output


def test_comps_help_works() -> None:
    result = runner.invoke(app, ["comps", "--help"])

    assert result.exit_code == 0
    assert "Fetch comparable sales for a listing." in result.output


def test_listings_help_works() -> None:
    result = runner.invoke(app, ["listings", "--help"])

    assert result.exit_code == 0
    assert "Manage saved listings." in result.output


def test_report_help_works() -> None:
    result = runner.invoke(app, ["report", "--help"])

    assert result.exit_code == 0
    assert "Generate a report." in result.output


def test_analyze_missing_required_fields_fails_cleanly() -> None:
    result = runner.invoke(app, ["analyze"])

    assert result.exit_code != 0
    assert "--title is required" in result.output


def test_comps_missing_query_fails_cleanly() -> None:
    result = runner.invoke(app, ["comps"])

    assert result.exit_code != 0
    assert "--query" in result.output


def test_listings_add_missing_required_fields_fails_cleanly() -> None:
    result = runner.invoke(app, ["listings", "add"])

    assert result.exit_code != 0
    assert "--title" in result.output


def test_listings_list_empty_command_works(db_path: Path) -> None:
    result = runner.invoke(app, ["listings", "list", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "No saved listings yet." in result.output


def test_analyze_saved_missing_listing_command_exits_cleanly() -> None:
    result = runner.invoke(app, ["analyze-saved", "listing-123"])

    assert result.exit_code != 0


def test_report_empty_command_works(db_path: Path) -> None:
    result = runner.invoke(app, ["report", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "No saved analyses found" in result.output

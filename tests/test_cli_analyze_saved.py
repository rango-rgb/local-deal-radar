import json
import shutil
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path

import pytest
from typer.testing import CliRunner

from local_deal_radar.cli import app
from local_deal_radar.config import MissingEbayCredentialsError

runner = CliRunner()


@pytest.fixture
def db_path() -> Path:
    base = Path(".test-data") / f"cli-analyze-saved-{uuid.uuid4().hex}"
    try:
        yield base / "deals.sqlite3"
    finally:
        if base.exists():
            shutil.rmtree(base)


def analyze_save_args(db_path: Path) -> list[str]:
    return [
        "analyze",
        "--mock",
        "--title",
        "Sony a6000 camera body",
        "--price",
        "220",
        "--category",
        "cameras",
        "--platform",
        "facebook",
        "--location",
        "Portland, OR",
        "--save",
        "--db-path",
        str(db_path),
    ]


def saved_counts(db_path: Path) -> tuple[int, int, int]:
    with closing(sqlite3.connect(db_path)) as connection:
        listings = connection.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
        analyses = connection.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        comps = connection.execute("SELECT COUNT(*) FROM comps").fetchone()[0]
    return listings, analyses, comps


def test_analyze_mock_save_creates_listing_analysis_and_comps(db_path: Path) -> None:
    result = runner.invoke(app, analyze_save_args(db_path))

    assert result.exit_code == 0
    assert "Saved listing id" in result.output
    listings, analyses, comps = saved_counts(db_path)
    assert listings == 1
    assert analyses == 1
    assert comps > 0


def test_analyze_mock_save_json_returns_ids(db_path: Path) -> None:
    result = runner.invoke(app, [*analyze_save_args(db_path), "--json"])
    payload = json.loads(result.output)

    assert result.exit_code == 0
    assert payload["listing_id"] == 1
    assert payload["analysis_id"] == 1
    assert payload["listing"]["id"] == 1


def test_analyze_saved_mock_analyzes_existing_listing_and_saves_new_analysis(db_path: Path) -> None:
    runner.invoke(app, analyze_save_args(db_path))

    result = runner.invoke(
        app,
        ["analyze-saved", "1", "--mock", "--db-path", str(db_path)],
    )

    assert result.exit_code == 0
    listings, analyses, comps = saved_counts(db_path)
    assert listings == 1
    assert analyses == 2
    assert comps > 0


def test_analyze_saved_missing_listing_exits_cleanly(db_path: Path) -> None:
    result = runner.invoke(
        app,
        ["analyze-saved", "999", "--mock", "--db-path", str(db_path)],
    )

    assert result.exit_code == 1
    assert "Saved listing 999 was not found." in result.output
    assert "Traceback" not in result.output


def test_analyze_saved_without_mock_missing_credentials_exits_cleanly(
    db_path: Path,
    monkeypatch,
) -> None:
    runner.invoke(app, analyze_save_args(db_path))

    class MissingCredentialsClient:
        def search_comps(self, query: str, category: str | None = None, limit: int = 10):
            raise MissingEbayCredentialsError(
                "Missing eBay credentials. Create .env from .env.example and set "
                "EBAY_CLIENT_ID and EBAY_CLIENT_SECRET."
            )

    monkeypatch.setattr("local_deal_radar.cli.EbayBrowseClient", MissingCredentialsClient)

    result = runner.invoke(app, ["analyze-saved", "1", "--db-path", str(db_path)])

    assert result.exit_code == 1
    assert "Missing eBay credentials" in result.output
    assert "Traceback" not in result.output


def test_report_command_still_returns_placeholder() -> None:
    result = runner.invoke(app, ["report"])

    assert result.exit_code == 0
    assert "Report command is not implemented yet." in result.output


def test_analyze_saved_json_includes_listing_and_analysis_ids(db_path: Path) -> None:
    runner.invoke(app, analyze_save_args(db_path))

    result = runner.invoke(
        app,
        ["analyze-saved", "1", "--mock", "--json", "--db-path", str(db_path)],
    )
    payload = json.loads(result.output)

    assert result.exit_code == 0
    assert payload["listing_id"] == 1
    assert payload["analysis_id"] == 2

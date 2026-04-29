import json
import shutil
import uuid
from pathlib import Path

import pytest
from typer.testing import CliRunner

from local_deal_radar.cli import app

runner = CliRunner()


@pytest.fixture
def db_path() -> Path:
    base = Path(".test-data") / f"cli-listings-{uuid.uuid4().hex}"
    try:
        yield base / "deals.sqlite3"
    finally:
        if base.exists():
            shutil.rmtree(base)


def add_listing_args(db_path: Path) -> list[str]:
    return [
        "listings",
        "add",
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
        "--db-path",
        str(db_path),
    ]


def test_listings_add_saves_listing_and_prints_id(db_path: Path) -> None:
    result = runner.invoke(app, add_listing_args(db_path))

    assert result.exit_code == 0
    assert "Saved listing 1" in result.output


def test_listings_list_shows_saved_listing(db_path: Path) -> None:
    runner.invoke(app, add_listing_args(db_path))

    result = runner.invoke(app, ["listings", "list", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "Sony a6000 camera body" in result.output
    assert "facebook" in result.output


def test_listings_list_json_returns_parseable_json(db_path: Path) -> None:
    runner.invoke(app, add_listing_args(db_path))

    result = runner.invoke(
        app,
        ["listings", "list", "--json", "--db-path", str(db_path)],
    )
    payload = json.loads(result.output)

    assert result.exit_code == 0
    assert payload[0]["id"] == 1
    assert payload[0]["title"] == "Sony a6000 camera body"


def test_listings_list_empty_db_gives_friendly_message(db_path: Path) -> None:
    result = runner.invoke(app, ["listings", "list", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "No saved listings yet." in result.output


def test_listings_add_missing_required_fields_fails_cleanly(db_path: Path) -> None:
    result = runner.invoke(
        app,
        ["listings", "add", "--title", "Sony", "--db-path", str(db_path)],
    )

    assert result.exit_code != 0
    assert "--price" in result.output


def test_db_path_uses_temporary_database(db_path: Path) -> None:
    result = runner.invoke(app, add_listing_args(db_path))

    assert result.exit_code == 0
    assert db_path.exists()

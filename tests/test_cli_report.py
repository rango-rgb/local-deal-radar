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
    base = Path(".test-data") / f"cli-report-{uuid.uuid4().hex}"
    try:
        yield base / "deals.sqlite3"
    finally:
        if base.exists():
            shutil.rmtree(base)


def save_analysis(db_path: Path, title: str, price: str = "220") -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            "--mock",
            "--title",
            title,
            "--price",
            price,
            "--category",
            "cameras",
            "--platform",
            "facebook",
            "--location",
            "Portland, OR",
            "--save",
            "--db-path",
            str(db_path),
        ],
    )
    assert result.exit_code == 0


def test_empty_db_report_shows_friendly_message(db_path: Path) -> None:
    result = runner.invoke(app, ["report", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "No saved analyses found. Run deal-radar analyze --save first." in result.output


def test_report_after_saved_mock_analysis_shows_opportunity_rows(db_path: Path) -> None:
    save_analysis(db_path, "Sony a6000 camera body")

    result = runner.invoke(app, ["report", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "Sony" in result.output
    assert "a6000" in result.output
    assert "MAYBE" in result.output
    assert "Active eBay comps are not sold comps" in result.output


def test_report_limit_limits_output(db_path: Path) -> None:
    save_analysis(db_path, "Sony a6000 camera body")
    save_analysis(db_path, "Canon EOS Rebel camera")

    result = runner.invoke(
        app,
        ["report", "--limit", "1", "--json", "--db-path", str(db_path)],
    )
    payload = json.loads(result.output)

    assert result.exit_code == 0
    assert payload["count"] == 1


def test_report_json_returns_parseable_json(db_path: Path) -> None:
    save_analysis(db_path, "Sony a6000 camera body")

    result = runner.invoke(app, ["report", "--json", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert json.loads(result.output)
    assert "\x1b[" not in result.output


def test_report_json_includes_count_and_opportunities(db_path: Path) -> None:
    save_analysis(db_path, "Sony a6000 camera body")

    result = runner.invoke(app, ["report", "--json", "--db-path", str(db_path)])
    payload = json.loads(result.output)

    assert payload["count"] == 1
    assert len(payload["opportunities"]) == 1


def test_report_json_includes_required_opportunity_fields(db_path: Path) -> None:
    save_analysis(db_path, "Sony a6000 camera body")

    result = runner.invoke(app, ["report", "--json", "--db-path", str(db_path)])
    opportunity = json.loads(result.output)["opportunities"][0]

    assert {
        "listing_id",
        "title",
        "expected_profit",
        "roi",
        "confidence_score",
        "decision",
        "warnings",
        "comp_count",
    } <= opportunity.keys()


def test_report_decision_and_min_profit_filters_work(db_path: Path) -> None:
    save_analysis(db_path, "Sony a6000 camera body", price="220")
    save_analysis(db_path, "Overpriced Sony a6000 camera body", price="390")

    result = runner.invoke(
        app,
        [
            "report",
            "--decision",
            "maybe",
            "--min-profit",
            "50",
            "--json",
            "--db-path",
            str(db_path),
        ],
    )
    payload = json.loads(result.output)

    assert result.exit_code == 0
    assert payload["count"] == 1
    assert payload["opportunities"][0]["title"] == "Sony a6000 camera body"


def test_report_db_path_uses_temporary_database(db_path: Path) -> None:
    save_analysis(db_path, "Sony a6000 camera body")

    result = runner.invoke(app, ["report", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert db_path.exists()


def test_report_does_not_require_ebay_credentials(db_path: Path, monkeypatch) -> None:
    save_analysis(db_path, "Sony a6000 camera body")
    monkeypatch.delenv("EBAY_CLIENT_ID", raising=False)
    monkeypatch.delenv("EBAY_CLIENT_SECRET", raising=False)

    result = runner.invoke(app, ["report", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "Missing eBay credentials" not in result.output

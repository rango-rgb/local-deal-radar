import json

from typer.testing import CliRunner

from local_deal_radar.cli import app
from local_deal_radar.config import MissingEbayCredentialsError

runner = CliRunner()


def test_comps_mock_exits_successfully() -> None:
    result = runner.invoke(
        app,
        ["comps", "--mock", "--query", "Sony a6000 camera body"],
    )

    assert result.exit_code == 0


def test_comps_mock_output_includes_plausible_comp_info() -> None:
    result = runner.invoke(
        app,
        ["comps", "--mock", "--query", "Sony a6000 camera body"],
    )

    assert result.exit_code == 0
    assert "Sony" in result.output
    assert "ebay_mock" in result.output


def test_comps_mock_json_returns_parseable_json() -> None:
    result = runner.invoke(
        app,
        ["comps", "--mock", "--query", "Sony a6000 camera body", "--json"],
    )

    payload = json.loads(result.output)
    assert result.exit_code == 0
    assert payload
    assert payload[0]["source"] == "ebay_mock"


def test_comps_without_mock_and_without_credentials_exits_cleanly(monkeypatch) -> None:
    class MissingCredentialsClient:
        def search_comps(self, query: str, category: str | None = None, limit: int = 10):
            raise MissingEbayCredentialsError(
                "Missing eBay credentials. Create .env from .env.example and set "
                "EBAY_CLIENT_ID and EBAY_CLIENT_SECRET."
            )

    monkeypatch.setattr("local_deal_radar.cli.EbayBrowseClient", MissingCredentialsClient)

    result = runner.invoke(app, ["comps", "--query", "Sony a6000 camera body"])

    assert result.exit_code == 1
    assert "Missing eBay credentials" in result.output
    assert "EBAY_CLIENT_ID" in result.output
    assert "EBAY_CLIENT_SECRET" in result.output
    assert "Traceback" not in result.output


def test_comps_missing_query_fails_cleanly() -> None:
    result = runner.invoke(app, ["comps", "--mock"])

    assert result.exit_code != 0
    assert "--query" in result.output

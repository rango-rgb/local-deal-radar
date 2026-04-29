from typer.testing import CliRunner

from local_deal_radar.cli import app
from local_deal_radar.config import MissingEbayCredentialsError

runner = CliRunner()


def test_analyze_mock_sony_a6000_exits_successfully() -> None:
    result = runner.invoke(
        app,
        [
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
        ],
    )

    assert result.exit_code == 0


def test_analyze_mock_output_includes_decision_and_expected_profit() -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            "--mock",
            "--title",
            "Sony a6000 camera body",
            "--price",
            "220",
            "--category",
            "cameras",
        ],
    )

    assert result.exit_code == 0
    assert "Decision" in result.output
    assert "Expected profit" in result.output


def test_analyze_without_mock_exits_cleanly_with_missing_credentials_message(monkeypatch) -> None:
    class MissingCredentialsClient:
        def search_comps(self, query: str, category: str | None = None, limit: int = 10):
            raise MissingEbayCredentialsError(
                "Missing eBay credentials. Create .env from .env.example and set "
                "EBAY_CLIENT_ID and EBAY_CLIENT_SECRET."
            )

    monkeypatch.setattr("local_deal_radar.cli.EbayBrowseClient", MissingCredentialsClient)

    result = runner.invoke(
        app,
        [
            "analyze",
            "--title",
            "Sony a6000 camera body",
            "--price",
            "220",
            "--category",
            "cameras",
        ],
    )

    assert result.exit_code == 1
    assert "Missing eBay credentials" in result.output
    assert "EBAY_CLIENT_ID" in result.output
    assert "Traceback" not in result.output


def test_analyze_mock_missing_required_fields_fails_cleanly() -> None:
    result = runner.invoke(app, ["analyze", "--mock", "--title", "Sony a6000 camera body"])

    assert result.exit_code != 0
    assert "--price is required" in result.output

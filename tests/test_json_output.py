import json

from typer.testing import CliRunner

from local_deal_radar.cli import app

runner = CliRunner()


def test_analyze_mock_json_returns_parseable_json() -> None:
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
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.output)


def test_json_output_includes_required_keys() -> None:
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
            "--json",
        ],
    )
    payload = json.loads(result.output)

    expected_keys = {
        "listing",
        "comps",
        "estimated_resale_value",
        "estimated_fees",
        "shipping_cost",
        "transaction_buffer",
        "pickup_cost",
        "risk_buffer",
        "expected_profit",
        "roi",
        "confidence_score",
        "condition_risk",
        "scam_risk",
        "hassle_score",
        "deal_score",
        "decision",
        "reasons",
        "warnings",
    }
    assert expected_keys <= payload.keys()


def test_json_output_contains_no_rich_formatting() -> None:
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
            "--json",
        ],
    )

    assert "\x1b[" not in result.output
    assert "╭" not in result.output
    assert result.output.lstrip().startswith("{")


def test_no_comps_json_returns_pass_and_warnings() -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            "--mock",
            "--title",
            "unknown item xyz",
            "--price",
            "220",
            "--category",
            "cameras",
            "--json",
        ],
    )
    payload = json.loads(result.output)

    assert result.exit_code == 0
    assert payload["decision"] == "pass"
    assert payload["comps"] == []
    assert payload["warnings"]

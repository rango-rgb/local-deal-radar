from typer.testing import CliRunner

from local_deal_radar.cli import app

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


def test_analyze_without_mock_exits_cleanly_with_live_not_implemented_message() -> None:
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

    assert result.exit_code == 0
    assert "Live eBay analysis is not implemented yet" in result.output
    assert "Use --mock" in result.output


def test_analyze_mock_missing_required_fields_fails_cleanly() -> None:
    result = runner.invoke(app, ["analyze", "--mock", "--title", "Sony a6000 camera body"])

    assert result.exit_code != 0
    assert "--price is required when using --mock" in result.output


def test_existing_placeholder_commands_still_work() -> None:
    commands = [
        ["comps"],
        ["listings", "add"],
        ["listings", "list"],
        ["analyze-saved", "listing-123"],
        ["report"],
    ]

    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0
        assert "not implemented yet" in result.output

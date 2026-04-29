# Local Deal Radar

Local Deal Radar is a local-first, human-in-the-loop resale intelligence CLI for
manually entered local marketplace listings.

This early version sets up packaging, a Typer CLI skeleton, local domain models,
category profiles, a conservative pure-Python scoring engine, deterministic mock
eBay-style comps, and CLI analysis wiring for offline mock runs. It does not
include marketplace scraping, live eBay integration, storage, saved reports, or
live marketplace imports.

## Development

```powershell
python -m pip install -e ".[dev]"
pytest -q
deal-radar --help
```

## Mock Analysis

```powershell
deal-radar analyze --mock --title "Sony a6000 camera body" --price 220 --category cameras
deal-radar analyze --mock --title "Sony a6000 camera body" --price 220 --category cameras --json
```

Live eBay analysis is intentionally not implemented yet. Use `--mock` for v0
offline analysis.

# Local Deal Radar

Local Deal Radar is a local-first, human-in-the-loop resale intelligence CLI for
manually entered local marketplace listings.

This early version sets up packaging, a Typer CLI skeleton, local domain models,
category profiles, a conservative pure-Python scoring engine, and tests. It does
not include marketplace scraping, eBay integration, storage, reports, or real CLI
analysis wiring.

## Development

```powershell
python -m pip install -e ".[dev]"
pytest -q
deal-radar --help
```

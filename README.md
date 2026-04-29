# Local Deal Radar

Local Deal Radar is a local-first, human-in-the-loop resale intelligence CLI for
manually entered local marketplace listings.

This Step 1 version only sets up packaging, a Typer CLI skeleton, and tests. It
does not include marketplace scraping, eBay integration, storage, scoring, or
real analysis logic.

## Development

```powershell
python -m pip install -e ".[dev]"
pytest -q
deal-radar --help
```

# Local Deal Radar

Local Deal Radar is a local-first, human-in-the-loop resale intelligence CLI for
manually entered local marketplace listings.

This early version sets up packaging, a Typer CLI skeleton, local domain models,
category profiles, a conservative pure-Python scoring engine, deterministic mock
eBay-style comps, and eBay Browse API analysis wiring. It does not include
marketplace scraping, storage, saved reports, or live marketplace imports.

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
deal-radar comps --mock --query "Sony a6000 camera body"
```

## Saved Listings

SQLite persistence is local-only and defaults to `data/deals.sqlite3`.

```powershell
deal-radar listings add --title "Sony a6000 camera body" --price 220 --category cameras --platform facebook --location "Portland, OR"
deal-radar listings list
deal-radar analyze --mock --title "Sony a6000 camera body" --price 220 --category cameras --save
deal-radar analyze-saved 1 --mock
```

Use `--db-path` on storage commands to point at a different local database.
Generated database files under `data/` should stay out of git.

## eBay Credentials

Live valuation uses the official eBay Browse API and requires eBay Developer
application credentials.

1. Create an eBay Developer account and application.
2. Copy `.env.example` to `.env`.
3. Set `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`.
4. Keep `.env` out of git.

eBay comps are active listings, not sold comps. Manual verification is required
before pursuing a deal.

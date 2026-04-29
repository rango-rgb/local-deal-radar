# Local Deal Radar

Local Deal Radar is a local-first, human-in-the-loop resale intelligence CLI for
manually entered local marketplace listings. It compares a local asking price
against eBay active comps, applies conservative resale costs and risk buffers,
then produces a pursue/maybe/pass decision. Listings, analyses, and comps are
stored locally in SQLite.

## What It Does

- Analyze manually entered local listings.
- Fetch live active comps from the official eBay Browse API.
- Run fully offline with deterministic mock eBay comps.
- Save listings and analyses to `data/deals.sqlite3`.
- Show a simple saved-opportunity report.
- Keep the operator in control of sourcing, verification, negotiation, and buying.

## What It Does Not Do

- No Facebook Marketplace or OfferUp scraping.
- No Craigslist scraping.
- No anti-bot, login-wall, or rate-limit bypassing.
- No browser automation.
- No auto-buying.
- No auto-messaging or seller outreach.
- No sold-comps scraping.

## Safe Sourcing Notes

For Facebook, OfferUp, Craigslist, and similar marketplaces, use manual
paste/entry workflows only. Verify the listing yourself, inspect condition,
confirm included parts, account for pickup/storage/shipping effort, and avoid
payments or seller behavior that look risky.

## eBay Credentials

Live valuation uses the official eBay Browse API.

1. Create an eBay Developer account and application.
2. Copy `.env.example` to `.env`.
3. Set `EBAY_CLIENT_ID`.
4. Set `EBAY_CLIENT_SECRET`.
5. Set `EBAY_MARKETPLACE_ID=EBAY_US` unless you need another marketplace.
6. Keep `.env` out of git.

Tests and `--mock` commands do not require eBay credentials.

## Quickstart

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q

deal-radar analyze --mock --title "Sony a6000 camera body" --price 220 --category cameras
deal-radar listings add --title "Sony a6000 camera body" --price 220 --category cameras --platform facebook --location "Portland, OR"
deal-radar analyze --mock --title "Sony a6000 camera body" --price 220 --category cameras --platform facebook --location "Portland, OR" --save
deal-radar report
```

SQLite persistence defaults to `data/deals.sqlite3`. Use `--db-path` on storage
commands to point at a different local database.

## Example Commands

Mock comps:

```powershell
deal-radar comps --mock --query "Sony a6000 camera body"
```

Live comps:

```powershell
deal-radar comps --query "Sony a6000 camera body" --limit 10
```

Mock analysis:

```powershell
deal-radar analyze --mock --title "Sony a6000 camera body" --price 220 --category cameras
```

Live analysis:

```powershell
deal-radar analyze --title "Sony a6000 camera body" --price 220 --category cameras --platform facebook --location "Portland, OR"
```

Save an analysis:

```powershell
deal-radar analyze --mock --title "Sony a6000 camera body" --price 220 --category cameras --platform facebook --location "Portland, OR" --save
```

Analyze a saved listing:

```powershell
deal-radar analyze-saved 1 --mock
```

Manage listings:

```powershell
deal-radar listings add --title "Sony a6000 camera body" --price 220 --category cameras --platform facebook --location "Portland, OR"
deal-radar listings list
```

Report:

```powershell
deal-radar report
deal-radar report --json
deal-radar report --limit 5
```

## Limitations

- eBay Browse API results are active listings, not sold comps.
- Active listings can be overpriced or stale.
- Manual verification is required before pursuing any deal.
- Condition, missing parts, shipping, storage, local pickup effort, and scam risk matter.
- The scoring is intentionally conservative and should say pass often.

## V0 Success Criteria

- Manually enter and test 50 Portland listings.
- See whether 3-5 genuinely promising leads emerge.
- Compare tool decisions against manual judgment.
- Tighten category profiles and scoring only after real observations.

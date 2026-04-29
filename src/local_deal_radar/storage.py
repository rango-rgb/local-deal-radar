"""SQLite persistence for saved listings and analyses."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from local_deal_radar.models import DealAnalysis, EbayComp, LocalListing

DEFAULT_DB_PATH = Path("data/deals.sqlite3")


class DealStore:
    """Small explicit SQLite store for v0 saved listings and analyses."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        """Create the database directory and schema if needed."""

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def save_listing(self, listing: LocalListing) -> LocalListing:
        """Insert a listing and return it with its database id populated."""

        self.initialize()
        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO listings (
                    title, price, category, url, platform, location, description, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    listing.title,
                    listing.price,
                    listing.category,
                    listing.url,
                    listing.platform,
                    listing.location,
                    listing.description,
                    _dt_to_text(listing.created_at),
                ),
            )
            listing_id = int(cursor.lastrowid)
            connection.commit()
        return listing.model_copy(update={"id": listing_id})

    def list_listings(self, limit: int = 50) -> list[LocalListing]:
        """Return saved listings newest first."""

        self.initialize()
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM listings
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return [_listing_from_row(row) for row in rows]

    def get_listing(self, listing_id: int) -> LocalListing | None:
        """Return a saved listing by id, or None."""

        self.initialize()
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT * FROM listings WHERE id = ?",
                (listing_id,),
            ).fetchone()
        if row is None:
            return None
        return _listing_from_row(row)

    def save_analysis(self, analysis: DealAnalysis) -> int:
        """Insert an analysis and its comps, saving the listing first if needed."""

        self.initialize()
        listing = analysis.listing
        if listing.id is None:
            listing = self.save_listing(listing)

        with closing(self._connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO analyses (
                    listing_id, estimated_resale_value, estimated_fees, shipping_cost,
                    transaction_buffer, pickup_cost, risk_buffer, expected_profit, roi,
                    confidence_score, condition_risk, scam_risk, hassle_score, deal_score,
                    decision, reasons_json, warnings_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    listing.id,
                    analysis.estimated_resale_value,
                    analysis.estimated_fees,
                    analysis.shipping_cost,
                    analysis.transaction_buffer,
                    analysis.pickup_cost,
                    analysis.risk_buffer,
                    analysis.expected_profit,
                    analysis.roi,
                    analysis.confidence_score,
                    analysis.condition_risk,
                    analysis.scam_risk,
                    analysis.hassle_score,
                    analysis.deal_score,
                    analysis.decision,
                    json.dumps(analysis.reasons),
                    json.dumps(analysis.warnings),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            analysis_id = int(cursor.lastrowid)
            connection.executemany(
                """
                INSERT INTO comps (
                    analysis_id, title, price, shipping, condition, url, source, item_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        analysis_id,
                        comp.title,
                        comp.price,
                        comp.shipping,
                        comp.condition,
                        comp.url,
                        comp.source,
                        comp.item_id,
                    )
                    for comp in analysis.comps
                ],
            )
            connection.commit()
        return analysis_id

    def get_latest_analysis_for_listing(self, listing_id: int) -> DealAnalysis | None:
        """Return the newest saved analysis for a listing, or None."""

        self.initialize()
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM analyses
                WHERE listing_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (listing_id,),
            ).fetchone()
            if row is None:
                return None
            return self._analysis_from_row(connection, row)

    def list_analyses(self, limit: int = 50) -> list[DealAnalysis]:
        """Return saved analyses newest first."""

        self.initialize()
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM analyses
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
            return [self._analysis_from_row(connection, row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _analysis_from_row(
        self,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> DealAnalysis:
        listing_row = connection.execute(
            "SELECT * FROM listings WHERE id = ?",
            (row["listing_id"],),
        ).fetchone()
        comp_rows = connection.execute(
            "SELECT * FROM comps WHERE analysis_id = ? ORDER BY id ASC",
            (row["id"],),
        ).fetchall()

        return DealAnalysis(
            listing=_listing_from_row(listing_row),
            comps=[_comp_from_row(comp_row) for comp_row in comp_rows],
            estimated_resale_value=row["estimated_resale_value"],
            estimated_fees=row["estimated_fees"],
            shipping_cost=row["shipping_cost"],
            transaction_buffer=row["transaction_buffer"],
            pickup_cost=row["pickup_cost"],
            risk_buffer=row["risk_buffer"],
            expected_profit=row["expected_profit"],
            roi=row["roi"],
            confidence_score=row["confidence_score"],
            condition_risk=row["condition_risk"],
            scam_risk=row["scam_risk"],
            hassle_score=row["hassle_score"],
            deal_score=row["deal_score"],
            decision=row["decision"],
            reasons=json.loads(row["reasons_json"]),
            warnings=json.loads(row["warnings_json"]),
        )


def _listing_from_row(row: sqlite3.Row) -> LocalListing:
    return LocalListing(
        id=row["id"],
        title=row["title"],
        price=row["price"],
        category=row["category"],
        url=row["url"],
        platform=row["platform"],
        location=row["location"],
        description=row["description"],
        created_at=row["created_at"],
    )


def _comp_from_row(row: sqlite3.Row) -> EbayComp:
    return EbayComp(
        title=row["title"],
        price=row["price"],
        shipping=row["shipping"],
        condition=row["condition"],
        url=row["url"],
        source=row["source"],
        item_id=row["item_id"],
    )


def _dt_to_text(value: datetime) -> str:
    return value.isoformat()


SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    url TEXT,
    platform TEXT,
    location TEXT,
    description TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL,
    estimated_resale_value REAL NOT NULL,
    estimated_fees REAL NOT NULL,
    shipping_cost REAL NOT NULL,
    transaction_buffer REAL NOT NULL,
    pickup_cost REAL NOT NULL,
    risk_buffer REAL NOT NULL,
    expected_profit REAL NOT NULL,
    roi REAL NOT NULL,
    confidence_score REAL NOT NULL,
    condition_risk REAL NOT NULL,
    scam_risk REAL NOT NULL,
    hassle_score REAL NOT NULL,
    deal_score REAL NOT NULL,
    decision TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(listing_id) REFERENCES listings(id)
);

CREATE TABLE IF NOT EXISTS comps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    shipping REAL NOT NULL,
    condition TEXT,
    url TEXT,
    source TEXT,
    item_id TEXT,
    FOREIGN KEY(analysis_id) REFERENCES analyses(id)
);
"""

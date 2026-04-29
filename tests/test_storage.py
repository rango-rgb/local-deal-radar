import sqlite3
import shutil
import uuid
from contextlib import closing
from pathlib import Path

import pytest

from local_deal_radar.models import EbayComp, LocalListing
from local_deal_radar.scoring import analyze_deal
from local_deal_radar.storage import DealStore


@pytest.fixture
def db_path() -> Path:
    base = Path(".test-data") / f"storage-{uuid.uuid4().hex}"
    try:
        yield base / "nested" / "deals.sqlite3"
    finally:
        if base.exists():
            shutil.rmtree(base)


def make_listing(title: str = "Sony a6000 camera body") -> LocalListing:
    return LocalListing(
        title=title,
        price=220,
        category="cameras",
        platform="facebook",
        location="Portland, OR",
    )


def make_analysis(listing: LocalListing):
    comps = [
        EbayComp(title="Comp 1", price=350, shipping=15, source="ebay_mock"),
        EbayComp(title="Comp 2", price=360, shipping=15, source="ebay_mock"),
        EbayComp(title="Comp 3", price=370, shipping=15, source="ebay_mock"),
        EbayComp(title="Comp 4", price=380, shipping=15, source="ebay_mock"),
    ]
    return analyze_deal(listing, comps)


def test_database_initializes_and_creates_expected_tables(db_path: Path) -> None:
    DealStore(db_path).initialize()

    with closing(sqlite3.connect(db_path)) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {"listings", "analyses", "comps"} <= table_names


def test_save_listing_returns_listing_with_id(db_path: Path) -> None:
    saved = DealStore(db_path).save_listing(make_listing())

    assert saved.id == 1
    assert saved.title == "Sony a6000 camera body"


def test_list_listings_returns_saved_listings_newest_first(db_path: Path) -> None:
    store = DealStore(db_path)
    first = store.save_listing(make_listing("First listing"))
    second = store.save_listing(make_listing("Second listing"))

    listings = store.list_listings()

    assert [listing.id for listing in listings] == [second.id, first.id]


def test_get_listing_returns_saved_listing(db_path: Path) -> None:
    store = DealStore(db_path)
    saved = store.save_listing(make_listing())

    loaded = store.get_listing(saved.id or 0)

    assert loaded == saved


def test_get_listing_returns_none_for_missing_id(db_path: Path) -> None:
    assert DealStore(db_path).get_listing(999) is None


def test_save_analysis_saves_analysis_and_comps(db_path: Path) -> None:
    store = DealStore(db_path)
    saved_listing = store.save_listing(make_listing())
    analysis = make_analysis(saved_listing)

    analysis_id = store.save_analysis(analysis)

    with closing(sqlite3.connect(db_path)) as connection:
        analysis_count = connection.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        comp_count = connection.execute("SELECT COUNT(*) FROM comps").fetchone()[0]
    assert analysis_id == 1
    assert analysis_count == 1
    assert comp_count == len(analysis.comps)


def test_get_latest_analysis_for_listing_rebuilds_analysis_with_comps(db_path: Path) -> None:
    store = DealStore(db_path)
    saved_listing = store.save_listing(make_listing())
    analysis = make_analysis(saved_listing)
    store.save_analysis(analysis)

    loaded = store.get_latest_analysis_for_listing(saved_listing.id or 0)

    assert loaded is not None
    assert loaded.listing.id == saved_listing.id
    assert loaded.comps[0].source == "ebay_mock"
    assert loaded.expected_profit == analysis.expected_profit


def test_list_analyses_returns_saved_analyses(db_path: Path) -> None:
    store = DealStore(db_path)
    first_listing = store.save_listing(make_listing("First"))
    second_listing = store.save_listing(make_listing("Second"))
    store.save_analysis(make_analysis(first_listing))
    store.save_analysis(make_analysis(second_listing))

    analyses = store.list_analyses()

    assert len(analyses) == 2
    assert analyses[0].listing.id == second_listing.id


def test_reasons_and_warnings_round_trip(db_path: Path) -> None:
    store = DealStore(db_path)
    saved_listing = store.save_listing(make_listing())
    analysis = make_analysis(saved_listing)
    store.save_analysis(analysis)

    loaded = store.get_latest_analysis_for_listing(saved_listing.id or 0)

    assert loaded is not None
    assert loaded.reasons == analysis.reasons
    assert loaded.warnings == analysis.warnings


def test_db_path_creates_parent_directory_if_missing(db_path: Path) -> None:
    assert not db_path.parent.exists()

    DealStore(db_path).initialize()

    assert db_path.exists()

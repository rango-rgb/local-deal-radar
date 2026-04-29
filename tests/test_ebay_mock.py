from local_deal_radar.ebay import MockEbayClient
from local_deal_radar.models import EbayComp


def test_mock_ebay_client_returns_ebay_comp_objects() -> None:
    comps = MockEbayClient().search_comps("Sony a6000 camera body", category="cameras")

    assert comps
    assert all(isinstance(comp, EbayComp) for comp in comps)


def test_mock_comps_have_ebay_mock_source() -> None:
    comps = MockEbayClient().search_comps("Sony a6000 camera body", category="cameras")

    assert {comp.source for comp in comps} == {"ebay_mock"}


def test_mock_ebay_client_respects_limit() -> None:
    comps = MockEbayClient().search_comps("Sony a6000 camera body", category="cameras", limit=2)

    assert len(comps) == 2


def test_camera_query_returns_enough_comps() -> None:
    comps = MockEbayClient().search_comps("Sony a6000 camera body", category="cameras")

    assert len(comps) >= 4


def test_unknown_or_no_comps_query_returns_empty_list() -> None:
    client = MockEbayClient()

    assert client.search_comps("no comps", category="cameras") == []
    assert client.search_comps("unknown item xyz", category="electronics") == []

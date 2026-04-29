"""Offline eBay-style comparable listings for local deal analysis."""

from local_deal_radar.categories import normalize_category
from local_deal_radar.models import EbayComp


NO_COMP_TERMS = ("no comps", "unknown item xyz")


class MockEbayClient:
    """Deterministic offline source of eBay-style comps."""

    def search_comps(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[EbayComp]:
        """Return normalized mock comps for a query and category."""

        if limit <= 0:
            return []

        normalized_query = query.strip().lower()
        if any(term in normalized_query for term in NO_COMP_TERMS):
            return []

        dataset_key = _dataset_key(normalized_query, category)
        comps = _COMP_DATASETS[dataset_key]
        return [comp.model_copy() for comp in comps[:limit]]


def _dataset_key(query: str, category: str | None) -> str:
    if "sony" in query and "a6000" in query:
        return "sony_a6000_camera_body"

    if category:
        normalized_category = normalize_category(category)
        if normalized_category in _COMP_DATASETS:
            return normalized_category

    normalized_query = normalize_category(query)
    for key in ("cameras", "lenses", "vintage_audio", "bikes", "electronics"):
        if key.rstrip("s") in query or key in query or key in normalized_query:
            return key

    return "default"


def _comp(
    item_id: str,
    title: str,
    price: float,
    shipping: float,
    condition: str,
) -> EbayComp:
    return EbayComp(
        item_id=item_id,
        title=title,
        price=price,
        shipping=shipping,
        condition=condition,
        source="ebay_mock",
    )


_COMP_DATASETS: dict[str, list[EbayComp]] = {
    "sony_a6000_camera_body": [
        _comp("mock-cam-a6000-001", "Sony Alpha a6000 24.3MP camera body", 345, 16, "Used"),
        _comp("mock-cam-a6000-002", "Sony a6000 mirrorless body black with battery", 360, 15, "Used"),
        _comp("mock-cam-a6000-003", "Sony ILCE-6000 a6000 body only tested", 370, 18, "Used"),
        _comp("mock-cam-a6000-004", "Sony a6000 camera body with charger", 385, 17, "Used"),
        _comp("mock-cam-a6000-005", "Sony Alpha a6000 body excellent condition", 395, 18, "Used"),
        _comp("mock-cam-a6000-006", "Sony a6000 body only clean sensor", 405, 19, "Used"),
    ],
    "cameras": [
        _comp("mock-cam-001", "Canon EOS Rebel T7 DSLR body", 245, 18, "Used"),
        _comp("mock-cam-002", "Nikon D3500 camera body with battery", 285, 18, "Used"),
        _comp("mock-cam-003", "Sony NEX mirrorless camera body", 225, 15, "Used"),
        _comp("mock-cam-004", "Panasonic Lumix GX85 camera body", 315, 16, "Used"),
        _comp("mock-cam-005", "Fujifilm X-T20 mirrorless body", 470, 20, "Used"),
    ],
    "lenses": [
        _comp("mock-lens-001", "Canon EF 50mm f/1.8 STM lens", 85, 8, "Used"),
        _comp("mock-lens-002", "Sony E 35mm f/1.8 OSS lens", 265, 10, "Used"),
        _comp("mock-lens-003", "Nikon AF-S DX 35mm f/1.8G lens", 145, 9, "Used"),
        _comp("mock-lens-004", "Sigma 30mm f/1.4 DC DN lens", 235, 10, "Used"),
        _comp("mock-lens-005", "Canon EF-S 24mm f/2.8 STM lens", 105, 8, "Used"),
    ],
    "vintage_audio": [
        _comp("mock-audio-001", "Pioneer SX vintage stereo receiver tested", 360, 45, "Used"),
        _comp("mock-audio-002", "Marantz 2220B stereo receiver working", 520, 55, "Used"),
        _comp("mock-audio-003", "Sansui 350A vintage receiver powers on", 210, 42, "Used"),
        _comp("mock-audio-004", "Technics SA receiver clean working", 185, 38, "Used"),
        _comp("mock-audio-005", "Yamaha CR vintage receiver serviced", 430, 50, "Used"),
    ],
    "bikes": [
        _comp("mock-bike-001", "Trek FX hybrid bicycle local pickup style comp", 265, 95, "Used"),
        _comp("mock-bike-002", "Specialized Sirrus commuter bike", 320, 110, "Used"),
        _comp("mock-bike-003", "Cannondale Quick hybrid bike", 295, 100, "Used"),
        _comp("mock-bike-004", "Giant Escape city bike", 250, 95, "Used"),
        _comp("mock-bike-005", "Surly steel commuter bicycle", 650, 125, "Used"),
    ],
    "electronics": [
        _comp("mock-elec-001", "Apple iPad 9th generation 64GB WiFi", 195, 12, "Used"),
        _comp("mock-elec-002", "Nintendo Switch console with dock", 205, 14, "Used"),
        _comp("mock-elec-003", "Bose QuietComfort headphones", 130, 10, "Used"),
        _comp("mock-elec-004", "Sony WH-1000XM4 headphones", 175, 10, "Used"),
        _comp("mock-elec-005", "Apple Watch Series 7 GPS", 155, 9, "Used"),
    ],
    "default": [
        _comp("mock-default-001", "Comparable used marketplace item", 80, 12, "Used"),
        _comp("mock-default-002", "Similar eBay-style comp tested", 95, 14, "Used"),
        _comp("mock-default-003", "Used item comparable listing", 105, 13, "Used"),
        _comp("mock-default-004", "Preowned item in good condition", 115, 15, "Used"),
        _comp("mock-default-005", "Comparable resale item clean", 125, 16, "Used"),
    ],
}

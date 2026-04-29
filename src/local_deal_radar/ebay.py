"""eBay comparable listing clients for local deal analysis."""

import base64
import time
from typing import Any

import httpx

from local_deal_radar.categories import normalize_category
from local_deal_radar.config import EbayConfig, MissingEbayCredentialsError, load_ebay_config
from local_deal_radar.models import EbayComp


NO_COMP_TERMS = ("no comps", "unknown item xyz")
PRODUCTION_API_BASE = "https://api.ebay.com"
SANDBOX_API_BASE = "https://api.sandbox.ebay.com"
TOKEN_PATH = "/identity/v1/oauth2/token"
BROWSE_SEARCH_PATH = "/buy/browse/v1/item_summary/search"
OAUTH_SCOPE = "https://api.ebay.com/oauth/api_scope"
MIN_SEARCH_LIMIT = 1
MAX_SEARCH_LIMIT = 50


class EbayApiError(Exception):
    """Raised for sanitized eBay API failures."""


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


class EbayBrowseClient:
    """Thin eBay Browse API client using application access tokens."""

    def __init__(
        self,
        config: EbayConfig | None = None,
        client: httpx.Client | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._config = config
        self._client = client or httpx.Client(timeout=timeout, transport=transport)
        self._access_token: str | None = None
        self._token_expires_at = 0.0

    @property
    def config(self) -> EbayConfig:
        if self._config is None:
            self._config = load_ebay_config()
        return self._config

    def get_application_token(self) -> str:
        """Fetch and cache an eBay application access token."""

        now = time.monotonic()
        if self._access_token and now < self._token_expires_at:
            return self._access_token

        config = self.config
        credentials = f"{config.client_id}:{config.client_secret}".encode("utf-8")
        basic_token = base64.b64encode(credentials).decode("ascii")

        try:
            response = self._client.post(
                f"{_api_base(config.environment)}{TOKEN_PATH}",
                data={
                    "grant_type": "client_credentials",
                    "scope": OAUTH_SCOPE,
                },
                headers={
                    "Authorization": f"Basic {basic_token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        except httpx.RequestError as exc:
            raise EbayApiError("Unable to reach eBay token endpoint.") from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise EbayApiError(
                f"eBay token request failed with status {response.status_code}."
            )

        payload = _json_response(response, "token")
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise EbayApiError("eBay token response did not include an access token.")

        expires_in = _coerce_float(payload.get("expires_in"), default=7200)
        self._access_token = access_token
        self._token_expires_at = now + max(0.0, expires_in - 60)
        return access_token

    def search_comps(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[EbayComp]:
        """Search active eBay Browse listings and normalize them into comps."""

        del category
        clamped_limit = _clamp_limit(limit)
        token = self.get_application_token()
        config = self.config

        try:
            response = self._client.get(
                f"{_api_base(config.environment)}{BROWSE_SEARCH_PATH}",
                params={"q": query, "limit": clamped_limit},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": config.marketplace_id,
                },
            )
        except httpx.RequestError as exc:
            raise EbayApiError("Unable to reach eBay Browse search endpoint.") from exc

        if response.status_code < 200 or response.status_code >= 300:
            raise EbayApiError(
                f"eBay Browse search failed with status {response.status_code}."
            )

        payload = _json_response(response, "Browse search")
        item_summaries = payload.get("itemSummaries")
        if not isinstance(item_summaries, list):
            return []

        comps: list[EbayComp] = []
        for item in item_summaries:
            if not isinstance(item, dict):
                continue
            comp = _normalize_item_summary(item)
            if comp is not None:
                comps.append(comp)
        return comps


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


def _api_base(environment: str) -> str:
    if environment == "sandbox":
        return SANDBOX_API_BASE
    return PRODUCTION_API_BASE


def _clamp_limit(limit: int) -> int:
    return max(MIN_SEARCH_LIMIT, min(MAX_SEARCH_LIMIT, int(limit)))


def _json_response(response: httpx.Response, label: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise EbayApiError(f"eBay {label} response was not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise EbayApiError(f"eBay {label} response was not a JSON object.")
    return payload


def _normalize_item_summary(item: dict[str, Any]) -> EbayComp | None:
    title = item.get("title")
    price = _money_value(item.get("price"))
    if not isinstance(title, str) or not title.strip() or price is None:
        return None

    try:
        return EbayComp(
            title=title,
            price=price,
            shipping=_shipping_cost(item),
            condition=item.get("condition"),
            url=item.get("itemWebUrl")
            or item.get("itemAffiliateWebUrl")
            or item.get("itemHref"),
            source="ebay",
            item_id=item.get("itemId"),
        )
    except ValueError:
        return None


def _shipping_cost(item: dict[str, Any]) -> float:
    shipping_options = item.get("shippingOptions")
    if not isinstance(shipping_options, list) or not shipping_options:
        return 0.0

    first_option = shipping_options[0]
    if not isinstance(first_option, dict):
        return 0.0
    return _money_value(first_option.get("shippingCost")) or 0.0


def _money_value(value: Any) -> float | None:
    if not isinstance(value, dict):
        return None
    return _coerce_float(value.get("value"))


def _coerce_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number < 0:
        return default
    return number


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

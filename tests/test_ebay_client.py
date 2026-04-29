import base64
from urllib.parse import parse_qs

import httpx
import pytest

from local_deal_radar.config import EbayConfig, MissingEbayCredentialsError
from local_deal_radar.ebay import (
    BROWSE_SEARCH_PATH,
    OAUTH_SCOPE,
    TOKEN_PATH,
    EbayApiError,
    EbayBrowseClient,
)
from local_deal_radar.models import EbayComp


def make_config() -> EbayConfig:
    return EbayConfig(
        client_id="client-id",
        client_secret="client-secret",
        marketplace_id="EBAY_US",
        environment="production",
    )


def make_search_payload() -> dict:
    return {
        "itemSummaries": [
            {
                "itemId": "v1|123",
                "title": "Sony a6000 camera body",
                "condition": "Used",
                "price": {"value": "349.99", "currency": "USD"},
                "shippingOptions": [
                    {"shippingCost": {"value": "14.50", "currency": "USD"}}
                ],
                "itemWebUrl": "https://www.ebay.com/itm/123",
            }
        ]
    }


def test_token_request_uses_correct_endpoint_method_form_and_basic_auth() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"access_token": "token", "expires_in": 7200})

    client = EbayBrowseClient(
        config=make_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.get_application_token() == "token"

    request = requests[0]
    expected_auth = base64.b64encode(b"client-id:client-secret").decode("ascii")
    body = parse_qs(request.content.decode("utf-8"))
    assert request.method == "POST"
    assert str(request.url) == "https://api.ebay.com/identity/v1/oauth2/token"
    assert request.headers["Authorization"] == f"Basic {expected_auth}"
    assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert body["grant_type"] == ["client_credentials"]
    assert body["scope"] == [OAUTH_SCOPE]


def test_search_request_uses_browse_endpoint_query_limit_and_headers() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == TOKEN_PATH:
            return httpx.Response(200, json={"access_token": "token", "expires_in": 7200})
        return httpx.Response(200, json=make_search_payload())

    client = EbayBrowseClient(
        config=make_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    comps = client.search_comps("Sony a6000 camera body", limit=7)

    search_request = requests[1]
    assert comps
    assert search_request.method == "GET"
    assert search_request.url.path == BROWSE_SEARCH_PATH
    assert search_request.url.params["q"] == "Sony a6000 camera body"
    assert search_request.url.params["limit"] == "7"
    assert search_request.headers["Authorization"] == "Bearer token"
    assert search_request.headers["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_US"


def test_token_is_cached_across_repeated_searches() -> None:
    token_request_count = 0
    search_request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_request_count, search_request_count
        if request.url.path == TOKEN_PATH:
            token_request_count += 1
            return httpx.Response(200, json={"access_token": "token", "expires_in": 7200})
        search_request_count += 1
        return httpx.Response(200, json=make_search_payload())

    client = EbayBrowseClient(
        config=make_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    client.search_comps("Sony a6000")
    client.search_comps("Sony a6000")

    assert token_request_count == 1
    assert search_request_count == 2


def test_normalizes_item_summaries_into_ebay_comps_with_shipping() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == TOKEN_PATH:
            return httpx.Response(200, json={"access_token": "token", "expires_in": 7200})
        return httpx.Response(200, json=make_search_payload())

    client = EbayBrowseClient(
        config=make_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    comps = client.search_comps("Sony a6000")

    assert len(comps) == 1
    comp = comps[0]
    assert isinstance(comp, EbayComp)
    assert comp.title == "Sony a6000 camera body"
    assert comp.price == 349.99
    assert comp.shipping == 14.50
    assert comp.condition == "Used"
    assert comp.url == "https://www.ebay.com/itm/123"
    assert comp.item_id == "v1|123"
    assert comp.source == "ebay"


def test_empty_item_summaries_returns_empty_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == TOKEN_PATH:
            return httpx.Response(200, json={"access_token": "token", "expires_in": 7200})
        return httpx.Response(200, json={"itemSummaries": []})

    client = EbayBrowseClient(
        config=make_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.search_comps("nothing") == []


def test_malformed_items_are_skipped() -> None:
    payload = {
        "itemSummaries": [
            {"title": "No price"},
            {"price": {"value": "10.00"}},
            {"title": "Bad price", "price": {"value": "not-a-number"}},
            {"title": "Good item", "price": {"value": "25.00"}},
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == TOKEN_PATH:
            return httpx.Response(200, json={"access_token": "token", "expires_in": 7200})
        return httpx.Response(200, json=payload)

    client = EbayBrowseClient(
        config=make_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    comps = client.search_comps("mixed")

    assert [comp.title for comp in comps] == ["Good item"]


def test_token_http_error_raises_friendly_ebay_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    client = EbayBrowseClient(
        config=make_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(EbayApiError) as exc_info:
        client.get_application_token()

    message = str(exc_info.value)
    assert "eBay token request failed with status 401" in message
    assert "client-secret" not in message
    assert "token" not in message.lower().replace("token request", "")


def test_search_http_error_raises_friendly_ebay_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == TOKEN_PATH:
            return httpx.Response(200, json={"access_token": "token", "expires_in": 7200})
        return httpx.Response(500, json={"error": "server_error"})

    client = EbayBrowseClient(
        config=make_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(EbayApiError) as exc_info:
        client.search_comps("Sony a6000")

    assert "eBay Browse search failed with status 500" in str(exc_info.value)


def test_missing_credentials_error_is_raised_cleanly(monkeypatch) -> None:
    def raise_missing() -> None:
        raise MissingEbayCredentialsError("Missing eBay credentials.")

    monkeypatch.setattr("local_deal_radar.ebay.load_ebay_config", raise_missing)
    client = EbayBrowseClient()

    with pytest.raises(MissingEbayCredentialsError):
        client.search_comps("Sony a6000")


def test_limit_is_clamped_to_sane_range() -> None:
    limits: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == TOKEN_PATH:
            return httpx.Response(200, json={"access_token": "token", "expires_in": 7200})
        limits.append(request.url.params["limit"])
        return httpx.Response(200, json=make_search_payload())

    client = EbayBrowseClient(
        config=make_config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    client.search_comps("Sony a6000", limit=999)
    client.search_comps("Sony a6000", limit=0)

    assert limits == ["50", "1"]

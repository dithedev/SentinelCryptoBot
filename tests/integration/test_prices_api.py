"""Integration tests for market price API endpoints.

These tests patch the service layer used by the route module. This keeps API
tests fast, deterministic, and independent from the real CoinGecko API.
"""

from decimal import Decimal

import pytest
from app.api.main import create_app
from app.core.exceptions import PriceProviderError, ValidationError
from app.services.prices_service import MarketPrice
from fastapi.testclient import TestClient


def test_list_prices_returns_supported_market_prices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /prices should return normalized market prices."""

    async def fake_get_supported_market_prices(
        _provider: object,
    ) -> list[MarketPrice]:
        """Return deterministic prices instead of calling the real provider."""
        return [
            MarketPrice(
                coin_id="bitcoin",
                symbol="BTC",
                name="Bitcoin",
                price_usd=Decimal("100000"),
            ),
            MarketPrice(
                coin_id="ethereum",
                symbol="ETH",
                name="Ethereum",
                price_usd=Decimal("3000.50"),
            ),
        ]

    monkeypatch.setattr(
        "app.api.routes.prices.get_supported_market_prices",
        fake_get_supported_market_prices,
    )

    client = TestClient(create_app())

    response = client.get("/prices")

    assert response.status_code == 200
    assert response.json() == [
        {
            "coin_id": "bitcoin",
            "symbol": "BTC",
            "name": "Bitcoin",
            "price_usd": "100000",
        },
        {
            "coin_id": "ethereum",
            "symbol": "ETH",
            "name": "Ethereum",
            "price_usd": "3000.50",
        },
    ]


def test_list_prices_returns_bad_gateway_when_provider_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /prices should return 502 when the price provider fails."""

    async def fake_get_supported_market_prices(
        _provider: object,
    ) -> list[MarketPrice]:
        """Simulate an external provider failure."""
        raise PriceProviderError("provider failed")

    monkeypatch.setattr(
        "app.api.routes.prices.get_supported_market_prices",
        fake_get_supported_market_prices,
    )

    client = TestClient(create_app())

    response = client.get("/prices")

    assert response.status_code == 502
    assert response.json() == {"detail": "Price provider is temporarily unavailable."}


def test_get_price_returns_one_market_price(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /prices/{coin_id} should return one normalized market price."""

    async def fake_get_coin_price(
        _provider: object,
        *,
        coin_id: str,
    ) -> MarketPrice:
        """Return a deterministic price for the requested coin id."""
        assert coin_id == "bitcoin"

        return MarketPrice(
            coin_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            price_usd=Decimal("100000"),
        )

    monkeypatch.setattr(
        "app.api.routes.prices.get_coin_price",
        fake_get_coin_price,
    )

    client = TestClient(create_app())

    response = client.get("/prices/bitcoin")

    assert response.status_code == 200
    assert response.json() == {
        "coin_id": "bitcoin",
        "symbol": "BTC",
        "name": "Bitcoin",
        "price_usd": "100000",
    }


def test_get_price_returns_bad_request_for_invalid_coin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /prices/{coin_id} should return 400 for unsupported coin ids."""

    async def fake_get_coin_price(
        _provider: object,
        *,
        coin_id: str,
    ) -> MarketPrice:
        """Simulate validation failure from the price service."""
        assert coin_id == "dogecoin"
        raise ValidationError("Unsupported coin id.")

    monkeypatch.setattr(
        "app.api.routes.prices.get_coin_price",
        fake_get_coin_price,
    )

    client = TestClient(create_app())

    response = client.get("/prices/dogecoin")

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported coin id."}


def test_get_price_returns_bad_gateway_when_provider_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /prices/{coin_id} should return 502 when provider lookup fails."""

    async def fake_get_coin_price(
        _provider: object,
        *,
        coin_id: str,
    ) -> MarketPrice:
        """Simulate an external provider failure."""
        assert coin_id == "bitcoin"
        raise PriceProviderError("provider failed")

    monkeypatch.setattr(
        "app.api.routes.prices.get_coin_price",
        fake_get_coin_price,
    )

    client = TestClient(create_app())

    response = client.get("/prices/bitcoin")

    assert response.status_code == 502
    assert response.json() == {"detail": "Price provider is temporarily unavailable."}

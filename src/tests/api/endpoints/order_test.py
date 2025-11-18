from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions import OrderSaveError
from app.schemas.order import OrderSide, OrderType


@pytest.mark.asyncio
async def test_create_order_success(async_client):
    """
    Test successful order creation via API.
    """
    order_data = {
        "instrument": "US0378331005",
        "type": "market",
        "quantity": 10,
        "side": "buy",
    }

    with patch("app.api.endpoints.order.OrderService") as mock_service_class:
        mock_service = AsyncMock()
        mock_order = AsyncMock()
        mock_order.id = 1
        mock_order.instrument = "US0378331005"
        mock_order.type = OrderType.MARKET
        mock_order.quantity = 10
        mock_order.side = OrderSide.BUY
        mock_order.limit_price = None
        mock_order.created_at = datetime(2025, 1, 1)
        mock_service.create_order = AsyncMock(return_value=mock_order)
        mock_service_class.return_value = mock_service
        response = await async_client.post("/api/orders", json=order_data)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["instrument"] == "US0378331005"
        assert data["type"] == "market"
        assert data["quantity"] == 10
        assert data["side"] == "buy"


@pytest.mark.asyncio
async def test_create_limit_order_success(async_client):
    """
    Test successful limit order creation via API.
    """
    order_data = {
        "instrument": "DE000A0Q4RZ3",
        "type": "limit",
        "quantity": 5,
        "side": "sell",
        "limit_price": 125.50,
    }

    with patch("app.api.endpoints.order.OrderService") as mock_service_class:
        mock_service = AsyncMock()
        mock_order = AsyncMock()
        mock_order.id = 2
        mock_order.instrument = "DE000A0Q4RZ3"
        mock_order.type = OrderType.LIMIT
        mock_order.quantity = 5
        mock_order.side = OrderSide.SELL
        mock_order.limit_price = 125.50
        mock_order.created_at = datetime(2025, 1, 1)
        mock_service.create_order = AsyncMock(return_value=mock_order)
        mock_service_class.return_value = mock_service
        response = await async_client.post("/api/orders", json=order_data)
        assert response.status_code == 201
        data = response.json()
        assert data["limit_price"] == 125.50


@pytest.mark.asyncio
async def test_create_order_invalid_data(async_client):
    """
    Test order creation with invalid data.
    """
    order_data = {"instrument": "US0378331005", "type": "market", "side": "buy"}

    response = await async_client.post("/api/orders", json=order_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_order_service_error(async_client):
    """
    Test order creation when service fails.
    """
    order_data = {
        "instrument": "US0378331005",
        "type": "market",
        "quantity": 10,
        "side": "buy",
    }

    with patch("app.api.endpoints.order.OrderService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.create_order = AsyncMock(side_effect=OrderSaveError("DB error"))
        mock_service_class.return_value = mock_service
        response = await async_client.post("/api/orders", json=order_data)
        assert response.status_code == 500
        assert (
            "Internal server error while placing the order"
            in response.json()["message"]
        )

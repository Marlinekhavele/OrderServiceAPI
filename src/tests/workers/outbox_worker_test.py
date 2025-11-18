from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.exceptions import OrderPlacementError
from app.models.order import Order
from app.schemas.order import OrderSide, OrderType
from app.workers.outbox_worker import process_outbox


@pytest.fixture
def mock_outbox_entry():
    """
    Mock outbox entry.
    """
    entry = MagicMock()
    entry.id = 1
    entry.order_id = 100
    entry.status = "pending"
    return entry


@pytest.fixture
def mock_order():
    """
    Mock order.
    """
    return Order(
        id=100,
        instrument="US0378331005",
        type=OrderType.MARKET,
        quantity=10,
        side=OrderSide.BUY,
    )


class TestOutboxWorker:
    """
    Tests for outbox worker functionality.
    """

    @pytest.mark.asyncio
    async def test_process_outbox_no_pending_entries(self):
        """
        Test worker when there are no pending entries.
        """
        with patch("app.workers.outbox_worker.SessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            with patch("app.workers.outbox_worker.OrderRepository") as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get_pending_outbox_entries = AsyncMock(return_value=[])
                mock_repo_class.return_value = mock_repo

                with patch(
                    "app.workers.outbox_worker.asyncio.sleep", new_callable=AsyncMock
                ) as mock_sleep:
                    mock_sleep.side_effect = KeyboardInterrupt

                    with pytest.raises(KeyboardInterrupt):
                        await process_outbox()

                    mock_repo.get_pending_outbox_entries.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_outbox_successful_placement(
        self, mock_outbox_entry, mock_order
    ):
        """
        Test worker successfully processes and places an order.
        """
        with patch("app.workers.outbox_worker.SessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            with patch("app.workers.outbox_worker.OrderRepository") as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get_pending_outbox_entries = AsyncMock(
                    side_effect=[[mock_outbox_entry], []]
                )
                mock_repo.get_order_by_id = AsyncMock(return_value=mock_order)
                mock_repo.update_outbox_entry = AsyncMock()
                mock_repo_class.return_value = mock_repo

                with patch(
                    "app.workers.outbox_worker.OrderService"
                ) as mock_service_class:
                    mock_service = AsyncMock()
                    mock_service._place_order_with_retry = AsyncMock()
                    mock_service_class.return_value = mock_service

                    with patch(
                        "app.workers.outbox_worker.asyncio.sleep",
                        new_callable=AsyncMock,
                    ) as mock_sleep:
                        mock_sleep.side_effect = [None, KeyboardInterrupt()]

                        with pytest.raises(KeyboardInterrupt):
                            await process_outbox()

                        mock_service._place_order_with_retry.assert_called_once_with(
                            mock_order
                        )

                        mock_repo.update_outbox_entry.assert_called_once_with(
                            mock_outbox_entry.id, "placed"
                        )

    @pytest.mark.asyncio
    async def test_process_outbox_placement_failure(
        self, mock_outbox_entry, mock_order
    ):
        """
        Test worker handles placement failure.
        """
        with patch("app.workers.outbox_worker.SessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            with patch("app.workers.outbox_worker.OrderRepository") as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get_pending_outbox_entries = AsyncMock(
                    side_effect=[[mock_outbox_entry], []]
                )
                mock_repo.get_order_by_id = AsyncMock(return_value=mock_order)
                mock_repo.update_outbox_entry = AsyncMock()
                mock_repo_class.return_value = mock_repo

                with patch(
                    "app.workers.outbox_worker.OrderService"
                ) as mock_service_class:
                    mock_service = AsyncMock()
                    mock_service._place_order_with_retry = AsyncMock(
                        side_effect=OrderPlacementError("Exchange down")
                    )
                    mock_service_class.return_value = mock_service

                    with patch(
                        "app.workers.outbox_worker.asyncio.sleep",
                        new_callable=AsyncMock,
                    ) as mock_sleep:
                        mock_sleep.side_effect = [None, KeyboardInterrupt()]

                        with pytest.raises(KeyboardInterrupt):
                            await process_outbox()

                        mock_repo.update_outbox_entry.assert_called_once_with(
                            mock_outbox_entry.id, "failed"
                        )

    @pytest.mark.asyncio
    async def test_process_outbox_order_not_found(self, mock_outbox_entry):
        """
        Test worker handles missing order gracefully.
        """
        with patch("app.workers.outbox_worker.SessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            with patch("app.workers.outbox_worker.OrderRepository") as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get_pending_outbox_entries = AsyncMock(
                    side_effect=[[mock_outbox_entry], []]
                )
                mock_repo.get_order_by_id = AsyncMock(return_value=None)
                mock_repo.update_outbox_entry = AsyncMock()
                mock_repo_class.return_value = mock_repo

                with patch(
                    "app.workers.outbox_worker.asyncio.sleep", new_callable=AsyncMock
                ) as mock_sleep:
                    mock_sleep.side_effect = [None, KeyboardInterrupt()]

                    with pytest.raises(KeyboardInterrupt):
                        await process_outbox()

                    mock_repo.update_outbox_entry.assert_called_once_with(
                        mock_outbox_entry.id, "failed"
                    )

    @pytest.mark.asyncio
    async def test_process_outbox_multiple_entries(self):
        """
        Test worker processes multiple pending entries.
        """
        entry1 = MagicMock(id=1, order_id=100)
        entry2 = MagicMock(id=2, order_id=101)
        order1 = Order(
            id=100,
            instrument="US0378331005",
            type=OrderType.MARKET,
            quantity=10,
            side=OrderSide.BUY,
        )
        order2 = Order(
            id=101,
            instrument="DE000A0Q4RZ3",
            type=OrderType.LIMIT,
            quantity=5,
            side=OrderSide.SELL,
            limit_price=125.50,
        )

        with patch("app.workers.outbox_worker.SessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            with patch("app.workers.outbox_worker.OrderRepository") as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get_pending_outbox_entries = AsyncMock(
                    side_effect=[[entry1, entry2], []]
                )
                mock_repo.get_order_by_id = AsyncMock(side_effect=[order1, order2])
                mock_repo.update_outbox_entry = AsyncMock()
                mock_repo_class.return_value = mock_repo

                with patch(
                    "app.workers.outbox_worker.OrderService"
                ) as mock_service_class:
                    mock_service = AsyncMock()
                    mock_service._place_order_with_retry = AsyncMock()
                    mock_service_class.return_value = mock_service

                    with patch(
                        "app.workers.outbox_worker.asyncio.sleep",
                        new_callable=AsyncMock,
                    ) as mock_sleep:
                        mock_sleep.side_effect = [None, KeyboardInterrupt()]

                        with pytest.raises(KeyboardInterrupt):
                            await process_outbox()

                        assert mock_service._place_order_with_retry.call_count == 2

                        assert mock_repo.update_outbox_entry.call_count == 2
                        mock_repo.update_outbox_entry.assert_has_calls(
                            [call(1, "placed"), call(2, "placed")], any_order=True
                        )

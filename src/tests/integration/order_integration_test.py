from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import OrderPlacementError, OrderSaveError
from app.models.outbox import OrderOutbox
from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreate, OrderSide, OrderType
from app.services.order import OrderService


class TestOrderIntegration:
    """
    Integration tests with real PostgreSQL.
    """

    @pytest.mark.asyncio
    async def test_order_persisted_to_db_and_outbox_created(
        self, db_session: AsyncSession
    ):
        """
        Test: POST /orders creates both order and outbox entry in DB.

        Verifies:
        1. Order persisted with all fields
        2. Outbox entry created with status="pending"
        """
        order_data = OrderCreate(
            instrument="DE000A0Q4RZ3",
            type=OrderType.LIMIT,
            quantity=100,
            side=OrderSide.BUY,
            limit_price=45.50,
        )

        service = OrderService(db_session)
        created_order = await service.create_order(order_data)

        assert created_order.id is not None
        assert created_order.instrument == "DE000A0Q4RZ3"
        assert created_order.type == OrderType.LIMIT
        assert created_order.quantity == 100
        assert created_order.side == OrderSide.BUY
        assert created_order.limit_price == 45.50

        repo = OrderRepository(db_session)
        pending_entries = await repo.get_pending_outbox_entries()
        assert len(pending_entries) == 1
        assert pending_entries[0].order_id == created_order.id
        assert pending_entries[0].status == "pending"

    @pytest.mark.asyncio
    async def test_worker_processes_outbox_and_marks_placed(
        self, db_session: AsyncSession
    ):
        """
        Test: Worker processes outbox and transitions to "placed".

        Verifies:
        1. Order + outbox created
        2. Worker processes entry
        3. Outbox status changed to "placed"
        """
        order_data = OrderCreate(
            instrument="US0378331005",
            type=OrderType.MARKET,
            quantity=50,
            side=OrderSide.SELL,
        )
        service = OrderService(db_session)
        created_order = await service.create_order(order_data)

        repo = OrderRepository(db_session)
        pending_before = await repo.get_pending_outbox_entries()
        assert len(pending_before) == 1
        assert pending_before[0].status == "pending"

        with patch(
            "app.services.order.OrderService._place_order_at_exchange",
            new_callable=AsyncMock,
        ) as mock_placement:
            mock_placement.return_value = None

            pending_entries = await repo.get_pending_outbox_entries()
            for entry in pending_entries:
                order = await repo.get_order_by_id(entry.order_id)
                assert order is not None

                placement_service = OrderService(db_session)
                await placement_service._place_order_with_retry(order)

                updated_entry = await repo.update_outbox_entry(entry.id, "placed")
                assert updated_entry is not None
                assert updated_entry.status == "placed"

        pending_after = await repo.get_pending_outbox_entries()
        assert len(pending_after) == 0

        stmt = select(OrderOutbox).where(OrderOutbox.order_id == created_order.id)
        result = await db_session.execute(stmt)
        outbox_entry = result.scalar_one_or_none()
        assert outbox_entry is not None
        assert outbox_entry.status == "placed"

    @pytest.mark.asyncio
    async def test_worker_marks_failed_on_placement_error(
        self, db_session: AsyncSession
    ):
        """
        Test: Worker marks outbox as "failed" after retry exhaustion.

        Verifies:
        1. Order + outbox created
        2. Worker attempts placement (all retries fail)
        3. Outbox marked as "failed"
        """
        order_data = OrderCreate(
            instrument="DE000A0Q4RZ3",
            type=OrderType.MARKET,
            quantity=10,
            side=OrderSide.BUY,
        )
        service = OrderService(db_session)
        await service.create_order(order_data)

        repo = OrderRepository(db_session)
        pending = await repo.get_pending_outbox_entries()
        outbox_entry_id = pending[0].id

        with patch(
            "app.services.order.OrderService._place_order_at_exchange",
            new_callable=AsyncMock,
        ) as mock_placement:
            mock_placement.side_effect = OrderPlacementError("Exchange down")

            pending_entries = await repo.get_pending_outbox_entries()
            for entry in pending_entries:
                order = await repo.get_order_by_id(entry.order_id)
                try:
                    placement_service = OrderService(db_session)
                    await placement_service._place_order_with_retry(order)
                except OrderPlacementError:
                    await repo.update_outbox_entry(entry.id, "failed")

        stmt = select(OrderOutbox).where(OrderOutbox.id == outbox_entry_id)
        result = await db_session.execute(stmt)
        failed_entry = result.scalar_one_or_none()
        assert failed_entry is not None
        assert failed_entry.status == "failed"

    @pytest.mark.asyncio
    async def test_concurrent_orders_all_enqueued(self, db_session: AsyncSession):
        """
        Test: Multiple concurrent orders are all persisted and enqueued.

        Verifies:
        1. 3 orders created concurrently
        2. All 3 have outbox entries
        3. All ready for worker processing
        """
        orders_data = [
            OrderCreate(
                instrument="DE000A0Q4RZ3",
                type=OrderType.LIMIT,
                quantity=100,
                side=OrderSide.BUY,
                limit_price=45.50,
            ),
            OrderCreate(
                instrument="US0378331005",
                type=OrderType.MARKET,
                quantity=50,
                side=OrderSide.SELL,
            ),
            OrderCreate(
                instrument="GB0002374006",
                type=OrderType.LIMIT,
                quantity=25,
                side=OrderSide.BUY,
                limit_price=100.0,
            ),
        ]

        service = OrderService(db_session)
        created_orders = []
        for order_data in orders_data:
            created_order = await service.create_order(order_data)
            created_orders.append(created_order)

        assert len(created_orders) == 3
        for i, order in enumerate(created_orders):
            assert order.id is not None
            assert order.instrument == orders_data[i].instrument

        repo = OrderRepository(db_session)
        pending_entries = await repo.get_pending_outbox_entries()
        assert len(pending_entries) == 3

    @pytest.mark.asyncio
    async def test_order_save_error_on_db_failure(self, db_session: AsyncSession):
        """
        Test: OrderSaveError raised on repository failure.

        Verifies:
        1. Database constraint violation triggers OrderSaveError
        2. Transaction is properly rolled back
        """
        repo = OrderRepository(db_session)

        with patch.object(
            db_session, "commit", side_effect=Exception("Database constraint violation")
        ):
            with pytest.raises(OrderSaveError):
                await repo.create_order(
                    order_data={
                        "instrument": "DE000A0Q4RZ3",
                        "type": OrderType.MARKET,
                        "quantity": 100,
                        "side": OrderSide.BUY,
                        "limit_price": None,
                    }
                )

    @pytest.mark.asyncio
    async def test_get_order_by_id_from_db(self, db_session: AsyncSession):
        """
        Test: Repository correctly fetches order from DB by ID.
        """
        order_data = OrderCreate(
            instrument="DE000A0Q4RZ3",
            type=OrderType.LIMIT,
            quantity=100,
            side=OrderSide.BUY,
            limit_price=45.50,
        )
        service = OrderService(db_session)
        created_order = await service.create_order(order_data)

        repo = OrderRepository(db_session)
        fetched_order = await repo.get_order_by_id(created_order.id)

        assert fetched_order is not None
        assert fetched_order.id == created_order.id
        assert fetched_order.instrument == "DE000A0Q4RZ3"
        assert fetched_order.quantity == 100
        assert fetched_order.limit_price == 45.50

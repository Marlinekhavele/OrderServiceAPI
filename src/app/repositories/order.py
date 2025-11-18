import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import OrderSaveError
from app.models.order import Order
from app.models.outbox import OrderOutbox

logger = logging.getLogger(__name__)


class OrderRepository:
    """
    Repository for Order and OrderOutbox database operations.

    Handles CRUD operations for orders and manages the outbox pattern
    for deferred order placement at the stock exchange.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: AsyncSession instance for database operations.
        """
        self.session = session

    async def get_order_by_id(self, order_id: int) -> Order | None:
        """
        Fetch an order by its ID.

        Args:
            order_id: The ID of the order to retrieve.

        Returns:
            Order object if found, None otherwise.
        """
        result = await self.session.get(Order, order_id)
        return result

    async def create_order(self, order_data: dict) -> Order:
        """
        Create and persist a new order.

        Args:
            order_data: Dictionary containing order fields (instrument, type, quantity, side, limit_price).

        Returns:
            Created Order object with ID assigned.

        Raises:
            OrderSaveError: If database commit fails.
        """
        new_order = Order(**order_data)
        try:
            self.session.add(new_order)
            await self.session.commit()
            await self.session.refresh(new_order)
            logger.info(
                f"Order created: id={new_order.id}, instrument={new_order.instrument}, type={new_order.type}, quantity={new_order.quantity}, side={new_order.side}, limit_price={new_order.limit_price}"
            )
            return new_order
        except Exception as exc:
            await self.session.rollback()
            logger.error(f"Failed to save order: {exc}")
            raise OrderSaveError("Failed to save order") from exc

    async def update_order(self, order_id: int, update_data: dict) -> Order | None:
        """
        Update an existing order.

        Args:
            order_id: The ID of the order to update.
            update_data: Dictionary of fields to update.

        Returns:
            Updated Order object if found, None otherwise.
        """
        order = await self.get_order_by_id(order_id)
        if order:
            for key, value in update_data.items():
                setattr(order, key, value)
            await self.session.commit()
            await self.session.refresh(order)
            return order
        return None

    async def delete_order(self, order_id: int) -> bool:
        """
        Delete an order by its ID.

        Args:
            order_id: The ID of the order to delete.

        Returns:
            True if deletion succeeded, False if order not found.
        """
        order = await self.get_order_by_id(order_id)
        if order:
            await self.session.delete(order)
            await self.session.commit()
            return True
        return False

    async def create_outbox_entry(self, order_id: int) -> OrderOutbox:
        """
        Create an outbox entry to track pending placement.

        Args:
            order_id: The ID of the order to enqueue for placement.

        Returns:
            Created OrderOutbox object with pending status.

        Raises:
            OrderSaveError: If database commit fails.
        """
        outbox = OrderOutbox(order_id=order_id, status="pending")
        try:
            self.session.add(outbox)
            await self.session.commit()
            await self.session.refresh(outbox)
            logger.info(
                f"Outbox entry created: id={outbox.id}, order_id={order_id}, status={outbox.status}"
            )
            return outbox
        except Exception as exc:
            await self.session.rollback()
            logger.error(f"Failed to create outbox entry for order {order_id}: {exc}")
            raise OrderSaveError("Failed to create outbox entry") from exc

    async def get_pending_outbox_entries(self) -> list[OrderOutbox]:
        """
        Fetch all pending outbox entries.

        Returns:
            List of OrderOutbox objects with status='pending'.
        """
        stmt = select(OrderOutbox).where(OrderOutbox.status == "pending")
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_outbox_entry(
        self, outbox_id: int, status: str
    ) -> OrderOutbox | None:
        """
        Update the status of an outbox entry.

        Args:
            outbox_id: The ID of the outbox entry to update.
            status: New status value (e.g., 'placed', 'failed').

        Returns:
            Updated OrderOutbox object if found, None otherwise.

        Raises:
            OrderSaveError: If database commit fails.
        """
        outbox = await self.session.get(OrderOutbox, outbox_id)
        if outbox:
            old_status = outbox.status
            outbox.status = status
            try:
                await self.session.commit()
                await self.session.refresh(outbox)
                logger.info(
                    f"Outbox entry updated: id={outbox_id}, status={old_status} -> {status}"
                )
                return outbox
            except Exception as exc:
                await self.session.rollback()
                logger.error(f"Failed to update outbox entry {outbox_id}: {exc}")
                raise OrderSaveError("Failed to update outbox entry") from exc
        logger.warning(f"Outbox entry {outbox_id} not found")
        return None

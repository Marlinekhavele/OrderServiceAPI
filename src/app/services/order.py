import asyncio
import logging
import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import OrderPlacementError
from app.models.order import Order
from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)


class OrderService:
    """
    Service layer for order operations.

    Handles order creation and enqueues placement via the outbox pattern
    to decouple the API from external stock exchange reliability.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the service with a database session.

        Args:
            session: AsyncSession instance for database operations.
        """
        self.repository = OrderRepository(session)

    async def create_order(self, order_data: OrderCreate) -> Order:
        """
        Create an order and enqueue it for placement via outbox.

        The order is persisted immediately, and placement is handled
        asynchronously by a background worker to ensure reliability
        and decouple external exchange failures from the API.

        Args:
            order_data: Validated order creation request.

        Returns:
            Created Order object.

        Raises:
            OrderSaveError: If database operations fail.
        """
        order = Order(
            instrument=order_data.instrument,
            type=order_data.type,
            quantity=order_data.quantity,
            side=order_data.side,
            limit_price=order_data.limit_price,
        )

        saved_order = await self.repository.create_order(
            order_data={
                "instrument": order.instrument,
                "type": order.type,
                "quantity": order.quantity,
                "side": order.side,
                "limit_price": order.limit_price,
            }
        )

        await self.repository.create_outbox_entry(order_id=saved_order.id)

        return saved_order

    async def _place_order_with_retry(self, order: Order, max_retries: int = 3):
        """
        Place order at exchange with exponential backoff retries.

        Args:
            order: Order object to place.
            max_retries: Maximum number of placement attempts.

        Raises:
            OrderPlacementError: If all retry attempts fail.
        """
        for attempt in range(max_retries):
            try:
                await self._place_order_at_exchange(order)
                logger.info(f"Order {order.id} placed successfully")
                return
            except OrderPlacementError as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Order {order.id} failed after {max_retries} attempts: {e}"
                    )
                    raise
                wait_time = 1
                logger.warning(
                    f"Order {order.id} placement failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

    async def _place_order_at_exchange(self, order: Order) -> None:
        """
        Dummy function that mimics stock exchange placement.

        Simulates external placement with ~10% failure rate and 0.5s latency
        to represent realistic external service behavior.

        Args:
            order: Order object to place.

        Raises:
            OrderPlacementError: If placement fails (10% chance).
        """
        if random.random() < 0.1:
            raise OrderPlacementError("Failed to place the order at the stock exchange")

        await asyncio.sleep(0.5)

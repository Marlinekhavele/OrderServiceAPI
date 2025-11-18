"""
Background worker to process pending orders from the outbox.

This worker polls the outbox table for pending orders and attempts
to place them at the stock exchange. It retries failed placements and
updates the outbox status accordingly.

Usage:
    cd src && poetry run python -m app.workers.outbox_worker
"""

import asyncio
import logging

from app.database.session import SessionLocal
from app.exceptions import OrderPlacementError
from app.repositories.order import OrderRepository
from app.services.order import OrderService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_outbox():
    """
    Poll and process pending outbox entries.
    """
    logger.info("Starting outbox worker...")

    while True:
        try:
            async with SessionLocal() as session:
                repository = OrderRepository(session)

                pending_entries = await repository.get_pending_outbox_entries()

                if pending_entries:
                    logger.info(f"Processing {len(pending_entries)} pending orders")

                for entry in pending_entries:
                    try:
                        order = await repository.get_order_by_id(entry.order_id)
                        if not order:
                            logger.warning(
                                f"Order {entry.order_id} not found (outbox id={entry.id})"
                            )
                            await repository.update_outbox_entry(entry.id, "failed")
                            continue

                        service = OrderService(session)
                        try:
                            await service._place_order_with_retry(order)
                            await repository.update_outbox_entry(entry.id, "placed")
                            logger.info(
                                f"Successfully placed order {order.id} (outbox id={entry.id})"
                            )
                        except OrderPlacementError as e:
                            logger.error(
                                f"Failed to place order {order.id} after retries: {e}"
                            )
                            await repository.update_outbox_entry(entry.id, "failed")

                    except Exception as e:
                        logger.error(
                            f"Unexpected error processing outbox entry {entry.id}: {e}"
                        )

            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(process_outbox())

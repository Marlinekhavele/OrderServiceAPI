import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db_session
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order import OrderService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    session: AsyncSession = Depends(get_db_session),
) -> OrderResponse:
    """
    Create a new order and enqueue it for placement.

    The order is persisted immediately (201 response), and placement
    is handled asynchronously by a background worker. This ensures
    the endpoint reliability is independent of the stock exchange.

    Args:
        order_data: Validated order creation request.
        session: Database session dependency.

    Returns:
        OrderResponse with created order details.

    Raises:
        HTTPException: 500 if order persistence fails.
    """
    logger.info(
        f"Received order request: instrument={order_data.instrument}, type={order_data.type}, quantity={order_data.quantity}, side={order_data.side}, limit_price={order_data.limit_price}"
    )
    service = OrderService(session)
    order = await service.create_order(order_data)
    logger.info(f"Order successfully created and enqueued: id={order.id}")
    return OrderResponse(
        id=order.id,
        instrument=order.instrument,
        type=order.type,
        quantity=order.quantity,
        side=order.side,
        limit_price=order.limit_price,
        created_at=order.created_at.isoformat(),
    )

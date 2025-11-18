from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums.order import OrderSide, OrderType


class OrderCreate(BaseModel):
    instrument: str = Field(..., min_length=1, description="ISIN of the stock")
    type: OrderType
    quantity: int = Field(..., gt=0)
    side: OrderSide
    limit_price: Optional[float] = Field(None, gt=0)

    @field_validator("limit_price")
    @classmethod
    def validate_limit_price(cls, v, info):
        """
        Ensure limit_price is provided for limit orders.
        """
        if info.data.get("type") == OrderType.LIMIT and v is None:
            raise ValueError("limit_price is required for limit orders")
        if info.data.get("type") == OrderType.MARKET and v is not None:
            raise ValueError("limit_price should not be provided for market orders")
        return v


class OrderResponse(BaseModel):
    id: int
    instrument: str
    type: OrderType
    quantity: int
    side: OrderSide
    limit_price: Optional[float]
    created_at: str

    class Config:
        from_attributes = True

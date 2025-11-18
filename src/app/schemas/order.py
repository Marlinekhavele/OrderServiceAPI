from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.enums.order import OrderSide, OrderType


class OrderCreate(BaseModel):
    instrument: str = Field(..., min_length=1, description="ISIN of the stock")
    type: OrderType
    quantity: int = Field(..., gt=0)
    side: OrderSide
    limit_price: Optional[float] = Field(None, gt=0)

    @model_validator(mode="after")
    def validate_limit_price(self):
        """
        Ensure limit_price rules depending on order type.
        """
        if self.type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if self.type == OrderType.MARKET and self.limit_price is not None:
            raise ValueError("limit_price should not be provided for market orders")
        return self


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

from sqlalchemy import Column, DateTime, Enum, Float, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base
from app.schemas.enums.order import OrderSide, OrderType


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    instrument = Column(String, nullable=False)
    type = Column(Enum(OrderType), nullable=False)
    quantity = Column(Integer, nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    limit_price = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __str__(self):
        return f"Order(id={self.id}, instrument={self.instrument}, type={self.type}, quantity={self.quantity}, side={self.side}, limit_price={self.limit_price}, created_at={self.created_at})"

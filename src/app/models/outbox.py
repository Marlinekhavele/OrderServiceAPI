from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database.base import Base


class OrderOutbox(Base):
    """
    Outbox table for tracking pending order placements.
    """

    __tablename__ = "order_outbox"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __str__(self):
        return f"OrderOutbox(id={self.id}, order_id={self.order_id}, status={self.status}, created_at={self.created_at}, updated_at={self.updated_at})"

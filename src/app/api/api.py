from fastapi import APIRouter

from app.api.endpoints.health import router as health_router
from app.api.endpoints.meta import router as meta_router
from app.api.endpoints.order import router as order_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(order_router, prefix="/orders", tags=["orders"])
api_router.include_router(meta_router, tags=["meta"])

import logging

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.api import api_router
from app.database.base import Base
from app.database.session import engine
from app.exceptions import OrderSaveError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OrderServiceAPI",
)


@app.exception_handler(OrderSaveError)
async def order_save_exception_handler(request: Request, exc: OrderSaveError):
    logger.exception(
        "OrderSaveError on %s %s: %s", request.method, request.url.path, exc
    )
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error while placing the order"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception on %s %s: %s", request.method, request.url.path, exc
    )
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error while placing the order"},
    )


@app.on_event("startup")
async def startup_event():
    """
    Create tables on startup
    """
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


app.include_router(api_router, prefix="/api")

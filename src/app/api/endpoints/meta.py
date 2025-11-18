import logging

from fastapi import APIRouter
from fastapi.requests import Request

from app.schemas.meta import Meta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meta")


@router.get("/", response_model=Meta)
async def meta(request: Request) -> Meta:
    logger.info(f"received request for {request.url}")
    return Meta(app_version="0.1.1")

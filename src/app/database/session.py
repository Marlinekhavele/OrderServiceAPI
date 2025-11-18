from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.settings import settings

engine = create_async_engine(
    settings.DB_URL,
    pool_pre_ping=True,
    future=True,
    connect_args={"server_settings": {"jit": "off"}},
)
# session maker
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
)

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from kimy.core.config import get_settings

settings = get_settings()

# NullPool: every session opens a fresh asyncpg connection bound to the current
# event loop. Avoids the "Future attached to a different loop" error that hits
# when FastAPI BackgroundTasks reuse pooled connections, especially with uvicorn
# --reload on Windows. For production we can swap back to the default QueuePool.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

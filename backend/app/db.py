import asyncpg
from app.config import settings

# Shared pool, created once on app startup and reused across all requests.
# Avoids opening a new Postgres connection per-request.
_pool: asyncpg.Pool | None = None


async def connect_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
    )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    """FastAPI dependency - yields the shared pool for a route to run queries against."""
    if _pool is None:
        raise RuntimeError("DB pool not initialized - did startup run?")
    return _pool

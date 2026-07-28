"""
Applies migrations/001_gold_schema.sql against DATABASE_URL using asyncpg.
Use this instead of `psql` if you don't have the Postgres client tools
installed locally (e.g. on Windows).

Usage:
    cd backend
    python -m scripts.run_migration
"""

import asyncio
from pathlib import Path

import asyncpg
from app.config import settings

MIGRATION_FILE = Path(__file__).resolve().parent.parent / "migrations" / "001_gold_schema.sql"


async def run_migration():
    sql = MIGRATION_FILE.read_text()
    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        await conn.execute(sql)
        print(f"Applied migration: {MIGRATION_FILE.name}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())

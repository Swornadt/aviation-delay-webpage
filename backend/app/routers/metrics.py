from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends
import asyncpg
from app.db import get_pool

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("/summary")
async def get_summary(pool: asyncpg.Pool = Depends(get_pool)):
    """PRD Req 2.1 - top-line KPIs for today, per GOLD_SCHEMA.md."""
    today_id = int(date.today().strftime("%Y%m%d"))

    async with pool.acquire() as conn:
        totals = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total_flights,
                AVG(dep_delay) FILTER (WHERE NOT cancelled) AS avg_dep_delay_minutes,
                (COUNT(*) FILTER (WHERE cancelled))::float / NULLIF(COUNT(*), 0) * 100 AS cancellation_rate_pct
            FROM fact_flights
            WHERE date_id = $1
            """,
            today_id,
        )

        top_hub = await conn.fetchrow(
            """
            SELECT a.airport_code, COUNT(*) AS flight_count
            FROM fact_flights f
            JOIN dim_airports a ON f.origin_id = a.airport_id
            WHERE f.date_id = $1
            GROUP BY a.airport_code
            ORDER BY flight_count DESC
            LIMIT 1
            """,
            today_id,
        )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_flights_today": totals["total_flights"] or 0,
        "avg_dep_delay_minutes": round(totals["avg_dep_delay_minutes"] or 0.0, 1),
        "cancellation_rate_pct": round(totals["cancellation_rate_pct"] or 0.0, 1),
        "top_congested_hub": top_hub["airport_code"] if top_hub else None,
    }


@router.get("/flight-paths")
async def get_flight_paths(pool: asyncpg.Pool = Depends(get_pool)):
    """PRD Req 2.2 - origin/dest coordinates for the geospatial map."""
    today_id = int(date.today().strftime("%Y%m%d"))

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                o.latitude  AS origin_lat,
                o.longitude AS origin_lon,
                d.latitude  AS dest_lat,
                d.longitude AS dest_lon,
                (f.dep_delay IS NOT NULL AND f.dep_delay > 15) AS delayed
            FROM fact_flights f
            JOIN dim_airports o ON f.origin_id = o.airport_id
            JOIN dim_airports d ON f.dest_id = d.airport_id
            WHERE f.date_id = $1 AND NOT f.cancelled
            LIMIT 500
            """,
            today_id,
        )

    return {"flight_paths": [dict(r) for r in rows]}

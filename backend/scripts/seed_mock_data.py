"""
Seeds Postgres with realistic mock data matching GOLD_SCHEMA.md.

This stands in for the real Gold Parquet -> Postgres loader until the
upstream PySpark pipeline finishes producing the Gold layer. Once real
Parquet files exist, replace this script's data source (the Python lists
below) with a Parquet read (e.g. pandas.read_parquet / pyarrow) -
the target tables and columns stay identical.

Usage:
    cd backend
    python -m scripts.seed_mock_data
"""

import asyncio
import random
from datetime import date, datetime, timedelta, timezone

import asyncpg
from app.config import settings

AIRPORTS = [
    ("ATL", "Hartsfield-Jackson Atlanta Intl", "Atlanta", "GA", 33.6407, -84.4277),
    ("ORD", "O'Hare Intl", "Chicago", "IL", 41.9742, -87.9073),
    ("DFW", "Dallas/Fort Worth Intl", "Dallas", "TX", 32.8998, -97.0403),
    ("DEN", "Denver Intl", "Denver", "CO", 39.8561, -104.6737),
    ("JFK", "John F. Kennedy Intl", "New York", "NY", 40.6413, -73.7781),
    ("LAX", "Los Angeles Intl", "Los Angeles", "CA", 33.9416, -118.4085),
    ("SFO", "San Francisco Intl", "San Francisco", "CA", 37.6213, -122.3790),
    ("SEA", "Seattle-Tacoma Intl", "Seattle", "WA", 47.4502, -122.3088),
]

CARRIERS = [
    ("UA", "United Airlines"),
    ("DL", "Delta Air Lines"),
    ("AA", "American Airlines"),
    ("WN", "Southwest Airlines"),
    ("B6", "JetBlue Airways"),
]

DELAY_CAUSES = ["weather", "carrier", "nas", "late_aircraft"]


async def seed():
    pool = await asyncpg.create_pool(dsn=settings.database_url)
    async with pool.acquire() as conn:
        async with conn.transaction():
            # --- dim_airports ---
            airport_ids = {}
            for code, name, city, state, lat, lon in AIRPORTS:
                row = await conn.fetchrow(
                    """
                    INSERT INTO dim_airports (airport_code, airport_name, city, state, latitude, longitude)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (airport_code) DO UPDATE SET airport_name = EXCLUDED.airport_name
                    RETURNING airport_id, airport_code
                    """,
                    code, name, city, state, lat, lon,
                )
                airport_ids[row["airport_code"]] = row["airport_id"]

            # --- dim_carriers ---
            carrier_ids = {}
            for code, name in CARRIERS:
                row = await conn.fetchrow(
                    """
                    INSERT INTO dim_carriers (carrier_code, carrier_name)
                    VALUES ($1, $2)
                    ON CONFLICT (carrier_code) DO UPDATE SET carrier_name = EXCLUDED.carrier_name
                    RETURNING carrier_id, carrier_code
                    """,
                    code, name,
                )
                carrier_ids[row["carrier_code"]] = row["carrier_id"]

            # --- dim_dates: today plus the past 6 days ---
            today = date.today()
            date_ids = {}
            for offset in range(7):
                d = today - timedelta(days=offset)
                date_id = int(d.strftime("%Y%m%d"))
                await conn.execute(
                    """
                    INSERT INTO dim_dates (date_id, full_date, day_of_week, is_weekend)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (date_id) DO NOTHING
                    """,
                    date_id, d, d.strftime("%A"), d.weekday() >= 5,
                )
                date_ids[d] = date_id

            # --- fact_flights: ~150 flights per day across the window ---
            airport_codes = list(airport_ids.keys())
            carrier_codes = list(carrier_ids.keys())

            flights = []
            for d, date_id in date_ids.items():
                for _ in range(150):
                    origin, dest = random.sample(airport_codes, 2)
                    carrier = random.choice(carrier_codes)
                    hour = random.randint(5, 22)
                    minute = random.choice([0, 15, 30, 45])
                    scheduled_dep = datetime(
                        d.year, d.month, d.day, hour, minute, tzinfo=timezone.utc
                    )

                    cancelled = random.random() < 0.015  # ~1.5% cancellation rate
                    if cancelled:
                        actual_dep = None
                        dep_delay = None
                        delay_cause = None
                    else:
                        delay_roll = random.random()
                        if delay_roll < 0.6:
                            dep_delay = round(random.uniform(-10, 10), 1)  # on-time-ish
                            delay_cause = None
                        else:
                            dep_delay = round(random.uniform(10, 90), 1)
                            delay_cause = random.choice(DELAY_CAUSES)
                        actual_dep = scheduled_dep + timedelta(minutes=dep_delay)

                    flights.append(
                        (
                            date_id,
                            carrier_ids[carrier],
                            airport_ids[origin],
                            airport_ids[dest],
                            scheduled_dep,
                            actual_dep,
                            dep_delay,
                            cancelled,
                            delay_cause,
                        )
                    )

            await conn.executemany(
                """
                INSERT INTO fact_flights
                    (date_id, carrier_id, origin_id, dest_id, scheduled_dep, actual_dep, dep_delay, cancelled, delay_cause)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                flights,
            )

            print(f"Seeded {len(flights)} flights across {len(date_ids)} days.")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(seed())

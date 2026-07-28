-- Gold star schema DDL for Postgres.
-- Run this once against the database in DATABASE_URL before running seed_mock_data.py.
-- See GOLD_SCHEMA.md for the data dictionary this matches.

CREATE TABLE IF NOT EXISTS dim_airports (
    airport_id      SERIAL PRIMARY KEY,
    airport_code    VARCHAR(3) UNIQUE NOT NULL,
    airport_name    VARCHAR(120) NOT NULL,
    city            VARCHAR(80),
    state           VARCHAR(2),
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_carriers (
    carrier_id      SERIAL PRIMARY KEY,
    carrier_code    VARCHAR(2) UNIQUE NOT NULL,
    carrier_name    VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_dates (
    date_id         INTEGER PRIMARY KEY,
    full_date       DATE UNIQUE NOT NULL,
    day_of_week     VARCHAR(9) NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_flights (
    flight_id       BIGSERIAL PRIMARY KEY,
    date_id         INTEGER NOT NULL REFERENCES dim_dates(date_id),
    carrier_id      INTEGER NOT NULL REFERENCES dim_carriers(carrier_id),
    origin_id       INTEGER NOT NULL REFERENCES dim_airports(airport_id),
    dest_id         INTEGER NOT NULL REFERENCES dim_airports(airport_id),
    scheduled_dep   TIMESTAMPTZ NOT NULL,
    actual_dep      TIMESTAMPTZ,
    dep_delay       DOUBLE PRECISION,
    cancelled       BOOLEAN NOT NULL DEFAULT FALSE,
    delay_cause     VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_fact_flights_date_id     ON fact_flights(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_flights_carrier_id  ON fact_flights(carrier_id);
CREATE INDEX IF NOT EXISTS idx_fact_flights_origin_id   ON fact_flights(origin_id);
CREATE INDEX IF NOT EXISTS idx_fact_flights_dest_id     ON fact_flights(dest_id);

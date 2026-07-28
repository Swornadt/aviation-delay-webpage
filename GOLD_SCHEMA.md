# GOLD_SCHEMA.md

Star schema contract for the aviation analytics platform. This is the
agreed target shape for the Gold layer — the upstream PySpark pipeline
should conform to this when `03_gold` is ready. Until then, this repo's
seed script populates Postgres directly against this same schema, so no
other code changes are needed when the real pipeline lands (only the
loader's data *source* changes, from a generator to real Parquet files).

---

## `dim_airports`

| Column        | Type         | Notes                          |
|---------------|--------------|---------------------------------|
| airport_id    | INTEGER PK   | surrogate key                   |
| airport_code  | VARCHAR(3)   | IATA code, e.g. 'ATL', unique   |
| airport_name  | VARCHAR(120) |                                  |
| city          | VARCHAR(80)  |                                  |
| state         | VARCHAR(2)   |                                  |
| latitude      | DOUBLE       |                                  |
| longitude     | DOUBLE       |                                  |

## `dim_carriers`

| Column        | Type         | Notes                          |
|---------------|--------------|---------------------------------|
| carrier_id    | INTEGER PK   | surrogate key                   |
| carrier_code  | VARCHAR(2)   | e.g. 'UA', 'DL', unique          |
| carrier_name  | VARCHAR(80)  | e.g. 'United Airlines'          |

## `dim_dates`

| Column        | Type         | Notes                          |
|---------------|--------------|---------------------------------|
| date_id       | INTEGER PK   | surrogate key, format YYYYMMDD  |
| full_date     | DATE         | unique                          |
| day_of_week   | VARCHAR(9)   | e.g. 'Monday'                   |
| is_weekend    | BOOLEAN      |                                  |

## `fact_flights`

| Column           | Type         | Notes                                          |
|------------------|--------------|-------------------------------------------------|
| flight_id        | BIGINT PK    | surrogate key                                    |
| date_id          | INTEGER FK   | -> dim_dates.date_id                             |
| carrier_id       | INTEGER FK   | -> dim_carriers.carrier_id                       |
| origin_id        | INTEGER FK   | -> dim_airports.airport_id                       |
| dest_id          | INTEGER FK   | -> dim_airports.airport_id                       |
| scheduled_dep    | TIMESTAMPTZ  |                                                   |
| actual_dep       | TIMESTAMPTZ  | nullable if cancelled                            |
| dep_delay        | DOUBLE       | minutes, can be negative (early)                 |
| cancelled        | BOOLEAN      |                                                   |
| delay_cause      | VARCHAR(20)  | 'weather' \| 'carrier' \| 'nas' \| 'late_aircraft' \| null |

### Indexes (Postgres — required for the <100ms KPI targets)
- `fact_flights(date_id)`
- `fact_flights(carrier_id)`
- `fact_flights(origin_id)`
- `fact_flights(dest_id)`

---

## Mapping to PRD endpoints

- `GET /api/v1/metrics/summary` → aggregates over `fact_flights` joined to `dim_dates` (today), plus a `GROUP BY origin_id` for `top_congested_hub`.
- `GET /api/v1/metrics/flight-paths` → `fact_flights` joined twice to `dim_airports` (origin + dest) for lat/lon pairs; `delayed` derived from `dep_delay > 0`.
- Copilot text-to-SQL system prompt should be seeded with this exact file's table/column list.

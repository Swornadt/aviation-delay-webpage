"""
Text-to-SQL copilot service.

Pipeline:
    1. generate_sql()      - LLM turns a natural-language question into a single
                              read-only SELECT against the gold schema.
    2. validate_select()   - defence-in-depth check before anything touches Postgres.
    3. run_query()         - executes read-only, with a statement timeout + row cap.
    4. synthesize_answer() - LLM turns the raw rows back into a short NL answer.

Any failure at any stage raises CopilotError with a message safe to show the
user - the router catches it and returns a clear explanation instead of a
guessed result.
"""

from __future__ import annotations

import json
import re

import asyncpg
from google import genai
from google.genai import types

from app.config import settings

_client: genai.Client | None = None


class CopilotError(Exception):
    """Raised at any stage of the pipeline with a user-facing message."""


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise CopilotError("GEMINI_API_KEY is not configured on the server.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


SCHEMA_DESCRIPTION = """
You can query the following Postgres tables (star schema). You only ever have
SELECT access - there is no write path.

dim_airports
    airport_id      INTEGER PRIMARY KEY
    airport_code    VARCHAR(3)     -- e.g. 'ATL', 'ORD'
    airport_name    VARCHAR(120)
    city            VARCHAR(80)
    state           VARCHAR(2)
    latitude        DOUBLE PRECISION
    longitude       DOUBLE PRECISION

dim_carriers
    carrier_id      INTEGER PRIMARY KEY
    carrier_code    VARCHAR(2)     -- e.g. 'UA', 'DL'
    carrier_name    VARCHAR(80)

dim_dates
    date_id         INTEGER PRIMARY KEY   -- format YYYYMMDD, e.g. 20260904
    full_date       DATE
    day_of_week     VARCHAR(9)
    is_weekend      BOOLEAN

fact_flights
    flight_id       BIGINT PRIMARY KEY
    date_id         INTEGER  REFERENCES dim_dates(date_id)
    carrier_id      INTEGER  REFERENCES dim_carriers(carrier_id)
    origin_id       INTEGER  REFERENCES dim_airports(airport_id)
    dest_id         INTEGER  REFERENCES dim_airports(airport_id)
    scheduled_dep   TIMESTAMPTZ
    actual_dep      TIMESTAMPTZ   -- NULL when cancelled
    dep_delay       DOUBLE PRECISION  -- minutes, NULL when cancelled
    cancelled       BOOLEAN
    delay_cause     VARCHAR(20)   -- one of: weather, carrier, nas, late_aircraft; NULL otherwise

Notes:
- "today" means the current date; for a DATE d, date_id = CAST(TO_CHAR(d, 'YYYYMMDD') AS INTEGER).
- A flight is "delayed" when dep_delay > 15.
- Join to dim_airports / dim_carriers to resolve human-readable codes/names
  instead of exposing raw *_id columns, unless the question explicitly asks for IDs.
- Always include a LIMIT (200 rows max) unless the question is a single aggregate.
"""

SQL_SYSTEM_PROMPT = f"""You are a senior data analyst who writes Postgres SQL.
Given a question about airline operations, write ONE single read-only SELECT
statement that answers it, using only the schema below. Output raw SQL only -
no prose, no markdown code fences.

If the question cannot be answered with this schema, output exactly:
NO_QUERY: <one sentence reason>

Schema:
{SCHEMA_DESCRIPTION}
"""

ANSWER_SYSTEM_PROMPT = """You are a helpful aviation operations analyst.
You're given the user's question and the resulting rows (as JSON) from a
query that already ran. Write a concise, direct natural-language answer using
ONLY the data provided. If the rows are empty, say so plainly rather than
guessing. Don't mention SQL or the query itself.
"""

_FORBIDDEN_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "truncate", "grant",
    "revoke", "create", "execute", "call", "copy", "vacuum", "merge",
    "into", "attach", "detach",
)

_ALLOWED_TABLES = {"dim_airports", "dim_carriers", "dim_dates", "fact_flights"}


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(sql)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def generate_sql(question: str) -> str:
    client = get_client()
    try:
        resp = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=SQL_SYSTEM_PROMPT,
                temperature=0,
            ),
        )
    except Exception as exc:  # network/auth/rate-limit errors from the SDK
        raise CopilotError(f"Couldn't reach the language model: {exc}") from exc

    raw = (resp.text or "").strip()
    sql = _strip_code_fence(raw)

    if sql.upper().startswith("NO_QUERY"):
        reason = sql.split(":", 1)[1].strip() if ":" in sql else "that's out of scope for this data."
        raise CopilotError(reason)

    if not sql:
        raise CopilotError("The model didn't return a query.")

    return sql


def validate_select(sql: str) -> str:
    """Defence-in-depth check, independent of the DB role. Returns cleaned SQL
    or raises CopilotError."""
    cleaned = sql.strip().rstrip(";").strip()

    if not cleaned:
        raise CopilotError("Generated an empty query.")

    if ";" in cleaned:
        raise CopilotError("Refusing to run multiple statements in one query.")

    lowered = cleaned.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise CopilotError("Generated query wasn't a SELECT statement.")

    for word in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{word}\b", lowered):
            raise CopilotError(f"Generated query contained a disallowed keyword: {word.upper()}.")

    referenced = set(re.findall(r"\b(dim_\w+|fact_\w+)\b", lowered))
    unknown = referenced - _ALLOWED_TABLES
    if unknown:
        raise CopilotError(f"Generated query referenced unknown table(s): {', '.join(sorted(unknown))}.")

    if "limit" not in lowered:
        cleaned = f"{cleaned}\nLIMIT {settings.copilot_max_rows}"

    return cleaned


async def run_query(pool: asyncpg.Pool, sql: str) -> list[dict]:
    timeout_ms = int(settings.copilot_query_timeout_seconds * 1000)
    try:
        async with pool.acquire() as conn:
            async with conn.transaction(readonly=True):
                await conn.execute(f"SET LOCAL statement_timeout = {timeout_ms}")
                rows = await conn.fetch(sql)
    except asyncpg.PostgresError as exc:
        raise CopilotError(f"The database rejected the query: {exc}") from exc
    except Exception as exc:
        raise CopilotError(f"Query execution failed: {exc}") from exc

    return [dict(r) for r in rows][: settings.copilot_max_rows]


async def synthesize_answer(question: str, rows: list[dict]) -> str:
    client = get_client()
    payload = json.dumps(rows, default=str)[:8000]  # guard against huge result sets

    try:
        resp = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=f"Question: {question}\n\nRows (JSON): {payload}",
            config=types.GenerateContentConfig(
                system_instruction=ANSWER_SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )
    except Exception as exc:
        raise CopilotError(f"Couldn't reach the language model: {exc}") from exc

    return (resp.choices[0].message.content or "").strip()
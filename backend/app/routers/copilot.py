from fastapi import APIRouter, Depends
import asyncpg
from pydantic import BaseModel

from app.db import get_pool
from app.services.copilot import (
    CopilotError,
    generate_sql,
    validate_select,
    run_query,
    synthesize_answer,
)

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    query: str
    generated_sql: str
    raw_data: list[dict]
    answer: str
    error: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, pool: asyncpg.Pool = Depends(get_pool)):
    """
    PRD Req 3.1-3.4 - Text-to-SQL copilot over the gold schema.

    1. Ask the LLM to translate the question into a single read-only SELECT.
    2. Validate it (single statement, SELECT-only, known tables only).
    3. Execute read-only against Postgres with a row cap + statement timeout.
    4. Ask the LLM to summarize the rows in plain language.

    Any failure returns a clear message in `answer` / `error` rather than a
    guessed result.
    """
    generated_sql = ""
    try:
        generated_sql = await generate_sql(req.prompt)
        safe_sql = validate_select(generated_sql)
        rows = await run_query(pool, safe_sql)
        answer = await synthesize_answer(req.prompt, rows)
        return ChatResponse(
            query=req.prompt,
            generated_sql=safe_sql,
            raw_data=rows,
            answer=answer,
        )
    except CopilotError as exc:
        return ChatResponse(
            query=req.prompt,
            generated_sql=generated_sql,
            raw_data=[],
            answer=f"I couldn't answer that: {exc}",
            error=str(exc),
        )
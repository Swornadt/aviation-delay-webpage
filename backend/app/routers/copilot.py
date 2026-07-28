from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    query: str
    generated_sql: str
    raw_data: list[dict]
    answer: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    PRD Req 3.1-3.4 - Text-to-SQL RAG copilot.

    TODO (Phase 3, once schema is finalized):
      1. Build a system prompt containing the real Postgres schema
         (table/column names, types, FKs) - see GOLD_SCHEMA.md.
      2. Call the LLM to generate SQL from req.prompt.
      3. Validate the SQL is a read-only SELECT before executing
         (run against a read-only DB role as a second safety net).
      4. Execute against Postgres, capture raw_data.
      5. Ask the LLM to synthesize a natural-language answer from raw_data.
      6. On any failure, return a clear error rather than a guessed answer.
    """
    return ChatResponse(
        query=req.prompt,
        generated_sql="-- not yet implemented",
        raw_data=[],
        answer="The copilot isn't wired up yet - this is a placeholder response.",
    )

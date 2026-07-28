import asyncio
import json
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/v1/stream", tags=["stream"])


@router.get("/live-flights")
async def live_flights(request: Request):
    """
    PRD Req 2.3 - pushes newly ingested flight records to the UI.

    TODO: replace the interval-based placeholder loop below with a real trigger,
    e.g. Postgres LISTEN/NOTIFY fired by the cron ingestion job, or a polling
    query against a "last_seen_id" watermark.
    """

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            # Placeholder heartbeat payload - swap for real new-flight rows.
            yield {
                "event": "heartbeat",
                "data": json.dumps({"status": "connected"}),
            }
            await asyncio.sleep(15)

    return EventSourceResponse(event_generator())

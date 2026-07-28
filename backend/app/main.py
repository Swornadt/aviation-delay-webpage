from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import connect_pool, close_pool
from app.routers import metrics, stream, copilot


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_pool()
    yield
    await close_pool()


app = FastAPI(title="Aviation Analytics Platform API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router)
app.include_router(stream.router)
app.include_router(copilot.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

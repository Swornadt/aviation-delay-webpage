# Real-Time Aviation Analytics Platform & RAG Copilot

## Repo layout

```
aviation-platform/
├── backend/                # FastAPI service (serving layer + RAG copilot)
│   ├── app/
│   │   ├── main.py         # app entrypoint, mounts routers
│   │   ├── config.py       # env var loading (pydantic-settings)
│   │   ├── db.py           # asyncpg connection pool
│   │   └── routers/
│   │       ├── metrics.py  # /api/v1/metrics/*
│   │       ├── stream.py   # /api/v1/stream/live-flights (SSE)
│   │       └── copilot.py  # /api/v1/copilot/chat
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Next.js + Tailwind
│   ├── app/
│   │   ├── page.tsx         # dashboard shell
│   │   ├── components/      # KpiTicker, FlightMap, DelayChart, CopilotDrawer
│   │   └── lib/api.ts       # typed fetch helpers for the backend
│   ├── package.json
│   ├── tailwind.config.ts
│   └── .env.local.example
└── docker-compose.yml        # Postgres for local dev
```

## Why it's structured this way

- **backend/app/routers/** — one file per feature area (metrics, stream, copilot), matching the PRD's endpoint groupings. Keeps `main.py` thin — it just mounts routers.
- **backend/app/db.py** — a single shared asyncpg pool, created on startup and injected via FastAPI dependency. Avoids opening a new connection per request.
- **frontend/app/components/** — each dashboard widget (KPI ticker, map, chart, chat drawer) is its own component so they can be built and tested independently, matching the phased build order (static data → live data → copilot).
- **docker-compose.yml** — spins up Postgres locally so the backend has something to talk to from day one, without needing a cloud DB yet.

## Getting started (step by step)

### 1. Start Postgres
```bash
docker compose up -d
```
This starts Postgres on `localhost:5432` with the credentials in `docker-compose.yml`.

### 2. Backend setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in DATABASE_URL / OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` — you should see the FastAPI auto-generated docs with the (currently stubbed) endpoints.

### 3. Frontend setup
```bash
cd frontend
npm install
cp .env.local.example .env.local   # fill in NEXT_PUBLIC_API_URL / Mapbox token
npm run dev
```
Visit `http://localhost:3000` — you should see the dashboard shell with placeholder cards.

### 4. Next steps (Phase 1 from the roadmap)
- Write the Gold Parquet → Postgres loader script (not yet included here).
- Implement the real SQL in `routers/metrics.py`.
- Wire `KpiTicker.tsx` to call the live `/summary` endpoint.

Everything above is intentionally a **skeleton** — routes return placeholder data, components render with mock props. This gets you a running end-to-end system (frontend → backend → Postgres) that you then fill in feature by feature, per the phased plan.

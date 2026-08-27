# NovaPath — Combined Modules 1–4

NovaPath now combines the Module 1–2 application flow (authentication,
profiles, dashboards, roadmap creation, and roadmap details) with the
Module 3–4 personalization and adaptive learning-plan flow.

The combined frontend lives in `Module 1&2/Novapath/frontend`. The FastAPI
service in `backend/` provides the Module 3–4 API and currently uses
`mock_roadmap.json` as the planner's roadmap source. The original Express
service remains available for Gemini roadmap generation and image analysis.

Built to match the team's tech spec:

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| AI | Google Gemini API |
| Auth | JWT / Supabase Auth (stubbed — see below) |

## What's here

## Run the combined application

Install the frontend dependencies, then start the NovaPath frontend:

```bash
cd "Module 1&2/Novapath/frontend"
npm install
npm run dev
```

In a second terminal, start the Module 3–4 FastAPI service:

```bash
cd backend
python -m venv venv
venv\\Scripts\\activate       # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the frontend URL printed by Vite, normally `http://localhost:5173`.
Sign in, open a roadmap, and select **Build personalized learning plan**.
The combined page sends personalization and learning-plan requests to
`http://localhost:8000`. The current planner adapter maps selected NovaPath
roadmaps to demo roadmap `101`, which matches `backend/mock_roadmap.json`.

For roadmap generation and image analysis, start the existing Express
service in a third terminal:

```bash
cd "Module 1&2/Novapath/backend"
npm install
npm run dev
```

It listens on `http://localhost:5000`.

## Original Module 3–4 standalone client

The top-level `frontend/` remains available as the isolated Module 3–4 demo.

## Project layout

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entrypoint
│   ├── database.py             # DB connection (Postgres, or SQLite for local dev)
│   ├── auth.py                 # Dev-mode auth stub — see "Auth" section below
│   ├── models/
│   │   ├── personalization.py  # Module 3 table
│   │   └── learning_plan.py    # Module 4 tables
│   ├── schemas/                # Pydantic request/response shapes
│   ├── routes/
│   │   ├── personalization.py  # Module 3 endpoints
│   │   └── learning_plan.py    # Module 4 endpoints
│   └── services/
│       ├── planner.py          # Deterministic scheduling algorithm
│       └── ai_planner.py       # Optional Gemini enrichment layer
├── mock_roadmap.json           # Stand-in for Module 2 until it exists
├── test_flow.py                # End-to-end smoke test
├── test_known_topics.py        # Smoke test for the "skip known topics" feature
└── requirements.txt

frontend/
└── src/
    ├── App.tsx
    ├── index.css                # Tailwind entry
    ├── api/client.ts            # Typed fetch wrapper for the backend API
    └── components/
        ├── PersonalizedSetup.tsx
        └── LearningPlanView.tsx
```

## How it works

```
Module 3 (Personalized Setup)
  UI form → POST /api/personalization → saved in DB

Module 4 (Learning Plan)
  POST /api/learning-plans/generate
    → reads saved preferences
    → reads roadmap (mock_roadmap.json for now, Module 2's API later)
    → runs the deterministic planning algorithm (planner.py)
    → optionally enriches task descriptions with AI (ai_planner.py)
    → saves plan + daily tasks to DB
    → returns day-by-day schedule

  POST /api/learning-plans/{id}/adapt
    → apply completed/missed status updates
    → recalculate remaining workload
    → rebuild only the future/incomplete portion of the schedule
```

The AI layer is **optional by design** — the app works fully without
an API key. Set `GEMINI_API_KEY` in `.env` to turn it on (get a free
key at https://aistudio.google.com/apikey).

### Skipping known topics

Module 3 accepts an optional `known_topic_ids` list — topics from
Module 2's roadmap the user already knows. Module 4's planner excludes
those entirely from the generated schedule (no tasks, no time
allocated), implementing the spec's "can skip topics the user already
knows" feature. See `test_known_topics.py` for a working example.

## Running the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# For real Postgres (team standard), run:
#   docker run --name training-db -e POSTGRES_PASSWORD=postgres \
#     -e POSTGRES_DB=training_platform -p 5432:5432 -d postgres
# For quick local testing without Postgres installed, edit .env and set:
#   DATABASE_URL=sqlite:///./dev.db

uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** for interactive Swagger docs
where you can try every endpoint directly.

Run the smoke tests any time to verify everything still works:

```bash
python test_flow.py
python test_known_topics.py
```

## Running the frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Visit **http://localhost:3000**. It's currently hardcoded to
`user_id=25, roadmap_id=101` and a `roadmapTopics` list matching
`mock_roadmap.json` (in `App.tsx`) — replace with real values once
Module 1 (auth) and Module 2 (roadmap selection) are wired in.

`npm run build` type-checks with `tsc` before building — run it before
committing to catch type errors early.

## API reference

### Module 3 — Personalization

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/personalization` | Save/replace a user's preferences for a roadmap (accepts optional `known_topic_ids`) |
| GET | `/api/personalization/{user_id}/{roadmap_id}` | Fetch saved preferences |
| PUT | `/api/personalization/{user_id}/{roadmap_id}` | Partially update preferences |

### Module 4 — Learning Plan

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/learning-plans/generate` | Generate a new day-by-day plan |
| GET | `/api/learning-plans/{plan_id}` | Fetch a plan by ID |
| GET | `/api/learning-plans/today/{user_id}` | Convenience: just today's tasks (for Module 5) |
| POST | `/api/learning-plans/{plan_id}/adapt` | Update task statuses & rebuild remaining schedule |

Full request/response schemas are in `backend/app/schemas/` and also
browsable live at `/docs`.

## Integration points — what changes when teammates' modules arrive

These are the **only** places that need edits when the rest of the team
is ready. Everything else (algorithm, DB schema, API contracts) stays as-is.

1. **Module 2 (Roadmap)** — replace `fetch_roadmap()` in
   `backend/app/routes/learning_plan.py` with a real HTTP call to their
   roadmap API instead of reading `mock_roadmap.json`. Also replace the
   hardcoded `roadmapTopics` array in `frontend/src/App.tsx` with a real
   fetch.
2. **Module 1 (Auth)** — a JWT verification stub already exists in
   `backend/app/auth.py` with instructions for wiring in real
   JWT/Supabase Auth. Right now `user_id` is trusted from the request
   body/path with no verification — swap route signatures to use
   `Depends(get_current_user_id)` once real tokens are available, and
   drop `user_id` from the request schemas (a security fix too, since
   nothing currently stops one user acting as another).
3. **Shared database** — point `DATABASE_URL` in `.env` at the team's
   real Postgres instance (the production target per spec). The
   `available_days` / `known_topic_ids` columns use a JSON-encoded-string
   type (`StringList` in `models/personalization.py`) that works on both
   SQLite and Postgres, so no migration is needed either way.
4. **Foreign keys** — `user_id` / `roadmap_id` / `topic_id` are currently
   loose integer references (no FK constraint) since Module 1/2's tables
   may not exist yet in this DB. Once they do, add real
   `ForeignKey("users.id")` / `ForeignKey("roadmaps.id")` constraints.
5. **Merging into one app** — instead of running this `main.py`
   directly, `include_router()` these two routers into the team's shared
   FastAPI app.
6. **CORS** — `main.py` currently allows `localhost:3000`/`5173` for
   local dev. Add the team's deployed frontend URL (Vercel) once it exists.

## Bonus: quiz question generator

`backend/app/services/ai_planner.py` also includes
`generate_quiz_questions(topic_title, skill_level, count)` — not wired
into any route yet, but ready for whoever builds Module 8 (Adaptive
Quiz System), since Gemini is already configured here. Same
fail-safe pattern: returns `[]` if AI isn't enabled or anything errors.

## Design notes

- **The algorithm decides the schedule; AI only polishes task text.**
  This avoids the common failure mode of "we prompted an LLM for a
  timetable and hoped for the best" — the schedule is always
  deterministic and explainable, which matters for a project review/viva.
- **Adaptation preserves history.** When you call `/adapt`, completed
  tasks are left untouched; only pending/missed tasks from today onward
  get rebuilt. Progress tracking (for Module 6/Analytics) stays accurate.
- **Everything is testable without AI or Postgres.** SQLite + no API key
  is enough to develop and demo the whole flow.

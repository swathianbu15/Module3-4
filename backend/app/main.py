"""
Module 3 + Module 4 — standalone FastAPI application.

Run with:
    uvicorn app.main:app --reload

Then visit http://localhost:8000/docs for interactive Swagger docs.

This app is self-contained (own DB tables, own routes) so it can run
independently while your teammates build Modules 1/2/5/6. When you
merge into the shared team repo, you'll likely:
  - mount these routers into the team's main FastAPI app instead of
    running this main.py directly, and
  - point database.py at the shared PostgreSQL database, and
  - replace fetch_roadmap() in routes/learning_plan.py with a real
    call to Module 2's API.
None of that requires changing the route/service logic itself.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes import personalization, learning_plan

# Create tables on startup (fine for dev; use Alembic migrations for prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Training Platform — Modules 3 & 4",
    description="Personalized Setup + AI Personalized Learning Plan",
    version="0.1.0",
)

# Allow the React dev server to call this API during local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(personalization.router)
app.include_router(learning_plan.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "modules": ["Module 3 - Personalized Setup", "Module 4 - Learning Plan"],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}

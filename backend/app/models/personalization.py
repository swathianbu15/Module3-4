"""
Module 3 — Personalized Setup

Stores what the user tells us about how they want to study a given
roadmap: goal, hours/day, available days, target date, skill level, and
which topics (if any) they want to skip because they already know them.

Team stack note: production DB is PostgreSQL (per project spec). The
StringList type below stores lists as JSON text so the same model also
runs on SQLite with zero code changes — useful for fast local dev/tests
without a Postgres server running, but DATABASE_URL should point at
Postgres for anything shared with the team.

NOTE on integration:
- user_id and roadmap_id are plain integers for now (no foreign key
  constraint to Module 1 / Module 2's tables), because those modules
  may not exist in this database yet. Once your teammates' tables
  exist, we can add real ForeignKey constraints pointing at
  users.id and roadmaps.id without changing the API.
- Auth: user_id is currently trusted from the request body/path. Once
  Module 1's JWT/Supabase Auth is live, this should instead be derived
  server-side from the verified token (see app/auth.py).
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, func
from sqlalchemy.types import TypeDecorator, VARCHAR
import json
from app.database import Base


class StringList(TypeDecorator):
    """
    Portable "array of strings" column.

    Stores a Python list as JSON text, so the same model works on both
    PostgreSQL and SQLite (handy for local dev / testing without a real
    Postgres server running). On real PostgreSQL you could switch this
    to sqlalchemy.dialects.postgresql.ARRAY(String) later if preferred —
    the rest of the code (schemas, routes) doesn't need to change either
    way since it just sees a Python list.
    """

    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


class UserLearningPreference(Base):
    __tablename__ = "user_learning_preferences"

    id = Column(Integer, primary_key=True, index=True)

    # References to other modules (loose reference for now — see note above)
    user_id = Column(Integer, nullable=False, index=True)
    roadmap_id = Column(Integer, nullable=False, index=True)

    learning_goal = Column(String, nullable=False)
    hours_per_day = Column(Integer, nullable=False)

    # Stored as an array of day names, e.g. ["Monday", "Wednesday", "Friday"]
    available_days = Column(StringList, nullable=False)

    target_date = Column(Date, nullable=False)
    skill_level = Column(String, nullable=False)  # beginner | intermediate | advanced

    # Topic IDs (from Module 2's roadmap) the user already knows and
    # wants the planner to skip. Feature from spec: "Can skip topics
    # the user already knows."
    known_topic_ids = Column(StringList, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

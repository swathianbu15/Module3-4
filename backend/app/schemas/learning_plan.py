"""
Pydantic schemas for Module 4 — AI Personalized Learning Plan.

Mirrors the API contract discussed with the team: roadmap topics come
in with an estimated_hours per topic (from Module 2), and this module
outputs a day-by-day breakdown of tasks.
"""

from datetime import date, datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, AliasChoices


# ---- Input: roadmap shape expected from Module 2 -----------------------

class RoadmapTopic(BaseModel):
    id: Union[int, str]
    title: str
    estimated_hours: float = Field(
        ...,
        gt=0,
        validation_alias=AliasChoices("estimated_hours", "estimatedHours"),
    )


class RoadmapInput(BaseModel):
    """
    This is the shape Module 2 is expected to provide (either by a real
    API call to their service, or — for now, while they're unavailable —
    passed in directly / read from mock_roadmap.json).
    """
    roadmap_id: int
    title: str
    topics: List[RoadmapTopic]


# ---- Generate plan request/response -------------------------------------

class GeneratePlanRequest(BaseModel):
    user_id: int
    roadmap_id: int
    # If provided, we use it directly instead of looking up saved
    # preferences — useful for testing without hitting the DB first.
    preference_id: Optional[int] = None
    use_ai: bool = Field(
        default=False,
        description="If true and an AI API key is configured, enrich tasks "
        "with AI-generated descriptions/breakdowns. Falls back to the "
        "plain algorithm if no key is set.",
    )


class TaskOut(BaseModel):
    id: int
    day_number: int
    date: date
    topic_title: str
    task_title: str
    description: Optional[str] = None
    estimated_minutes: int
    task_type: str
    status: str

    class Config:
        from_attributes = True


class DayOut(BaseModel):
    day: int
    date: date
    tasks: List[TaskOut]
    total_minutes: int


class LearningPlanResponse(BaseModel):
    plan_id: int
    user_id: int
    roadmap_id: int
    start_date: date
    target_date: date
    status: str
    days: List[DayOut]


# ---- Adaptation -----------------------------------------------------------

class TaskProgressUpdate(BaseModel):
    task_id: int
    status: str = Field(..., pattern="^(completed|missed|in_progress|pending)$")


class AdaptPlanRequest(BaseModel):
    task_updates: List[TaskProgressUpdate] = Field(default_factory=list)
    # Optional: recalculate as of a specific date (defaults to today)
    as_of_date: Optional[date] = None

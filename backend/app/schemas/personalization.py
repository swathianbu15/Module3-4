"""
Pydantic schemas for Module 3 — Personalized Setup.

These define exactly what the API accepts and returns. Keeping this
separate from the SQLAlchemy models means the database can change
shape without breaking the API contract your teammates rely on.
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SkillLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


VALID_DAYS = {
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
}


class PersonalizationCreate(BaseModel):
    user_id: int
    roadmap_id: int
    learning_goal: str = Field(..., min_length=1, max_length=255)
    hours_per_day: int = Field(..., gt=0, le=16)
    available_days: List[str] = Field(..., min_length=1)
    target_date: date
    skill_level: SkillLevel
    known_topic_ids: List[int] = Field(
        default_factory=list,
        description="Topic IDs (from Module 2's roadmap) the user already "
        "knows. Module 4 will skip these when generating the plan.",
    )

    @field_validator("available_days")
    @classmethod
    def validate_days(cls, value: List[str]) -> List[str]:
        invalid = [d for d in value if d not in VALID_DAYS]
        if invalid:
            raise ValueError(
                f"Invalid day(s): {invalid}. Must be full weekday names, "
                f"e.g. 'Monday'."
            )
        return value

    @field_validator("target_date")
    @classmethod
    def validate_future_date(cls, value: date) -> date:
        if value <= date.today():
            raise ValueError("target_date must be in the future")
        return value


class PersonalizationUpdate(BaseModel):
    """All fields optional — only send what you want to change."""

    learning_goal: Optional[str] = None
    hours_per_day: Optional[int] = Field(None, gt=0, le=16)
    available_days: Optional[List[str]] = None
    target_date: Optional[date] = None
    skill_level: Optional[SkillLevel] = None
    known_topic_ids: Optional[List[int]] = None

    @field_validator("available_days")
    @classmethod
    def validate_days(cls, value):
        if value is None:
            return value
        invalid = [d for d in value if d not in VALID_DAYS]
        if invalid:
            raise ValueError(f"Invalid day(s): {invalid}")
        return value


class PersonalizationResponse(BaseModel):
    id: int
    user_id: int
    roadmap_id: int
    learning_goal: str
    hours_per_day: int
    available_days: List[str]
    target_date: date
    skill_level: str
    known_topic_ids: List[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

"""
Module 4 — AI Personalized Learning Plan

Two tables:
- learning_plans: one row per generated plan (a "container")
- daily_learning_tasks: one row per task, linked to a plan + day number

This mirrors the structure the team's Module 5 (Daily Tasks) and
Module 6 (Analytics) will eventually query against, per the API
contract described in the architecture doc.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False, index=True)
    roadmap_id = Column(Integer, nullable=False, index=True)

    # Link back to the preferences that generated this plan
    preference_id = Column(
        Integer, ForeignKey("user_learning_preferences.id"), nullable=True
    )

    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)

    # active | completed | abandoned | superseded (replaced by an adapted plan)
    status = Column(String, nullable=False, default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tasks = relationship(
        "DailyLearningTask",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="DailyLearningTask.day_number",
    )


class DailyLearningTask(Base):
    __tablename__ = "daily_learning_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)

    day_number = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)

    # topic_id is a loose reference to Module 2's topic records (see note
    # in personalization.py re: cross-module foreign keys)
    topic_id = Column(Integer, nullable=True)
    topic_title = Column(String, nullable=False)

    task_title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    estimated_minutes = Column(Integer, nullable=False)

    # learning | practice | quiz | revision | project
    task_type = Column(String, nullable=False, default="learning")

    # pending | completed | missed | in_progress
    status = Column(String, nullable=False, default="pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plan = relationship("LearningPlan", back_populates="tasks")

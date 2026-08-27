"""
Module 4 — AI Personalized Learning Plan API routes.

    POST   /api/learning-plans/generate
    GET    /api/learning-plans/{plan_id}
    POST   /api/learning-plans/{plan_id}/adapt

Also includes:
    GET    /api/learning-plans/today/{user_id}
a convenience endpoint your Module 5 (Daily Tasks) teammate will likely
want, matching the "GET /learning-plan/today" example from the
architecture discussion.
"""

import json
import os
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.personalization import UserLearningPreference
from app.models.learning_plan import LearningPlan, DailyLearningTask
from app.schemas.learning_plan import (
    GeneratePlanRequest,
    AdaptPlanRequest,
    LearningPlanResponse,
    RoadmapInput,
    DayOut,
)
from app.services.planner import (
    get_study_dates,
    distribute_topics_across_days,
    validate_plan,
)
from app.services.ai_planner import enhance_plan_with_ai

router = APIRouter(prefix="/api/learning-plans", tags=["Module 4 - Learning Plan"])

MOCK_ROADMAP_PATH = Path(__file__).resolve().parents[2] / "mock_roadmap.json"


def fetch_roadmap(roadmap_id: int) -> RoadmapInput:
    """
    Fetch roadmap + topics for the given roadmap_id.

    INTEGRATION POINT: Module 2 (Roadmap Management) doesn't exist yet
    in this environment, so this reads from mock_roadmap.json instead.

    When Module 2's API is ready, replace the body of this function with
    an HTTP call, e.g.:

        response = httpx.get(f"{MODULE_2_BASE_URL}/roadmaps/{roadmap_id}")
        response.raise_for_status()
        return RoadmapInput(**response.json())

    Nothing else in this file needs to change — everything downstream
    just consumes a RoadmapInput object.
    """
    if not MOCK_ROADMAP_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Roadmap source not available: mock_roadmap.json missing "
            "and Module 2 integration is not yet configured.",
        )

    with open(MOCK_ROADMAP_PATH) as f:
        data = json.load(f)

    if data.get("roadmap_id") != roadmap_id:
        raise HTTPException(
            status_code=404,
            detail=f"Roadmap {roadmap_id} not found (mock data only has "
            f"roadmap_id={data.get('roadmap_id')} — add more roadmaps to "
            f"mock_roadmap.json, or connect Module 2's real API).",
        )

    return RoadmapInput(**data)


@router.post("/generate", response_model=LearningPlanResponse, status_code=201)
def generate_plan(payload: GeneratePlanRequest, db: Session = Depends(get_db)):
    # 1. Get the user's saved preferences
    if payload.preference_id:
        prefs = db.get(UserLearningPreference, payload.preference_id)
    else:
        prefs = (
            db.query(UserLearningPreference)
            .filter_by(user_id=payload.user_id, roadmap_id=payload.roadmap_id)
            .first()
        )

    if not prefs:
        raise HTTPException(
            status_code=404,
            detail="No saved preferences found. Complete Module 3 setup "
            "(POST /api/personalization) before generating a plan.",
        )

    # 2. Get the roadmap (from Module 2, or mock data for now)
    roadmap = fetch_roadmap(payload.roadmap_id)

    # 3. Run the deterministic planning algorithm
    study_dates = get_study_dates(
        start_date=date.today(),
        target_date=prefs.target_date,
        available_days=prefs.available_days,
    )
    planned_days = distribute_topics_across_days(
        topics=roadmap.topics,
        study_dates=study_dates,
        hours_per_day=prefs.hours_per_day,
        known_topic_ids=prefs.known_topic_ids,
    )

    warnings = validate_plan(planned_days, roadmap.topics)

    # 4. Optionally enrich with AI (no-op if ANTHROPIC_API_KEY isn't set)
    if payload.use_ai:
        planned_days = enhance_plan_with_ai(
            planned_days, prefs.skill_level, prefs.learning_goal
        )

    # 5. Persist to the database
    # Mark any previous active plan for this user/roadmap as superseded
    db.query(LearningPlan).filter_by(
        user_id=payload.user_id, roadmap_id=payload.roadmap_id, status="active"
    ).update({"status": "superseded"})

    plan = LearningPlan(
        user_id=payload.user_id,
        roadmap_id=payload.roadmap_id,
        preference_id=prefs.id,
        start_date=date.today(),
        target_date=prefs.target_date,
        status="active",
    )
    db.add(plan)
    db.flush()  # get plan.id before creating tasks

    for day in planned_days:
        for task in day.tasks:
            db.add(
                DailyLearningTask(
                    plan_id=plan.id,
                    day_number=day.day_number,
                    date=day.date,
                    topic_title=task.topic_title,
                    task_title=task.task_title,
                    description=task.description,
                    estimated_minutes=task.estimated_minutes,
                    task_type=task.task_type,
                    status="pending",
                )
            )

    db.commit()
    db.refresh(plan)

    result = _plan_to_response(plan)
    if warnings:
        # FastAPI response_model won't include extra fields by default,
        # so warnings are logged server-side; the frontend can also call
        # this same logic itself if it wants to display them. See README
        # for how to surface these in the UI if desired.
        print(f"[Module 4] Plan {plan.id} warnings: {warnings}")

    return result


@router.get("/{plan_id}", response_model=LearningPlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.get(LearningPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Learning plan not found.")
    return _plan_to_response(plan)


@router.get("/today/{user_id}", response_model=DayOut)
def get_today_tasks(user_id: int, db: Session = Depends(get_db)):
    """
    Convenience endpoint for Module 5 (Daily Tasks) to fetch just
    today's tasks for a user's active plan.
    """
    plan = (
        db.query(LearningPlan)
        .filter_by(user_id=user_id, status="active")
        .order_by(LearningPlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No active learning plan found.")

    today = date.today()
    today_tasks = [t for t in plan.tasks if t.date == today]

    if not today_tasks:
        raise HTTPException(
            status_code=404, detail="No tasks scheduled for today on this plan."
        )

    day_number = today_tasks[0].day_number
    return DayOut(
        day=day_number,
        date=today,
        tasks=today_tasks,
        total_minutes=sum(t.estimated_minutes for t in today_tasks),
    )


@router.post("/{plan_id}/adapt", response_model=LearningPlanResponse)
def adapt_plan(
    plan_id: int, payload: AdaptPlanRequest, db: Session = Depends(get_db)
):
    """
    Adaptive re-planning (Phase 5 from the architecture doc).

    Approach:
    1. Apply the task status updates the caller sent (completed/missed/etc).
    2. Identify remaining incomplete workload (pending + missed tasks
       from today onward).
    3. Recalculate available study days between now and the original
       target date.
    4. Re-run the same deterministic algorithm on just the remaining
       workload, replacing future pending tasks with the new schedule.

    This keeps past/completed tasks untouched (so progress history is
    preserved) and only rebuilds what's left.
    """
    plan = db.get(LearningPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Learning plan not found.")

    as_of = payload.as_of_date or date.today()

    # 1. Apply status updates
    task_by_id = {t.id: t for t in plan.tasks}
    for update in payload.task_updates:
        task = task_by_id.get(update.task_id)
        if task is None:
            raise HTTPException(
                status_code=400,
                detail=f"Task {update.task_id} does not belong to plan {plan_id}.",
            )
        task.status = update.status
    db.flush()

    # 2. Find remaining incomplete workload (group by topic to rebuild
    #    RoadmapTopic-like objects for the planner)
    incomplete = [
        t for t in plan.tasks if t.date >= as_of and t.status != "completed"
    ]

    if not incomplete:
        # Nothing left to adapt — plan is on track or finished.
        db.commit()
        return _plan_to_response(plan)

    from collections import defaultdict
    from app.schemas.learning_plan import RoadmapTopic as RoadmapTopicSchema

    remaining_minutes_by_topic = defaultdict(int)
    for t in incomplete:
        remaining_minutes_by_topic[t.topic_title] += t.estimated_minutes

    remaining_topics = [
        RoadmapTopicSchema(id=i, title=title, estimated_hours=minutes / 60)
        for i, (title, minutes) in enumerate(remaining_minutes_by_topic.items())
    ]

    # 3. Recalculate study days from as_of to the original target_date
    prefs = db.get(UserLearningPreference, plan.preference_id) if plan.preference_id else None
    available_days = prefs.available_days if prefs else ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    hours_per_day = prefs.hours_per_day if prefs else 2

    study_dates = get_study_dates(
        start_date=as_of, target_date=plan.target_date, available_days=available_days
    )

    new_days = distribute_topics_across_days(
        topics=remaining_topics, study_dates=study_dates, hours_per_day=hours_per_day
    )

    # 4. Remove old incomplete future tasks, insert the rebuilt schedule
    for t in incomplete:
        db.delete(t)
    db.flush()

    # Re-number days to continue from wherever the plan currently is
    max_existing_day = max((t.day_number for t in plan.tasks), default=0)
    for offset, day in enumerate(new_days, start=1):
        for task in day.tasks:
            db.add(
                DailyLearningTask(
                    plan_id=plan.id,
                    day_number=max_existing_day + offset,
                    date=day.date,
                    topic_title=task.topic_title,
                    task_title=task.task_title,
                    description=task.description,
                    estimated_minutes=task.estimated_minutes,
                    task_type=task.task_type,
                    status="pending",
                )
            )

    db.commit()
    db.refresh(plan)
    return _plan_to_response(plan)


def _plan_to_response(plan: LearningPlan) -> LearningPlanResponse:
    from collections import defaultdict

    tasks_by_day = defaultdict(list)
    for t in plan.tasks:
        tasks_by_day[t.day_number].append(t)

    days = [
        DayOut(
            day=day_number,
            date=tasks[0].date,
            tasks=tasks,
            total_minutes=sum(t.estimated_minutes for t in tasks),
        )
        for day_number, tasks in sorted(tasks_by_day.items())
    ]

    return LearningPlanResponse(
        plan_id=plan.id,
        user_id=plan.user_id,
        roadmap_id=plan.roadmap_id,
        start_date=plan.start_date,
        target_date=plan.target_date,
        status=plan.status,
        days=days,
    )

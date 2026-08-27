"""
Module 3 — Personalized Setup API routes.

    POST   /api/personalization
    GET    /api/personalization/{user_id}/{roadmap_id}
    PUT    /api/personalization/{user_id}/{roadmap_id}
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.personalization import UserLearningPreference
from app.schemas.personalization import (
    PersonalizationCreate,
    PersonalizationUpdate,
    PersonalizationResponse,
)

router = APIRouter(prefix="/api/personalization", tags=["Module 3 - Personalization"])


@router.post("", response_model=PersonalizationResponse, status_code=201)
def create_or_replace_preferences(
    payload: PersonalizationCreate, db: Session = Depends(get_db)
):
    """
    Save a user's learning preferences for a given roadmap.
    If preferences already exist for this (user_id, roadmap_id) pair,
    they are replaced — a user re-doing the setup flow shouldn't create
    duplicate rows.
    """
    existing = (
        db.query(UserLearningPreference)
        .filter_by(user_id=payload.user_id, roadmap_id=payload.roadmap_id)
        .first()
    )

    if existing:
        for field, value in payload.model_dump(exclude={"user_id", "roadmap_id"}).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    record = UserLearningPreference(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{user_id}/{roadmap_id}", response_model=PersonalizationResponse)
def get_preferences(user_id: int, roadmap_id: int, db: Session = Depends(get_db)):
    record = (
        db.query(UserLearningPreference)
        .filter_by(user_id=user_id, roadmap_id=roadmap_id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=404,
            detail="No preferences found for this user/roadmap combination.",
        )
    return record


@router.put("/{user_id}/{roadmap_id}", response_model=PersonalizationResponse)
def update_preferences(
    user_id: int,
    roadmap_id: int,
    payload: PersonalizationUpdate,
    db: Session = Depends(get_db),
):
    record = (
        db.query(UserLearningPreference)
        .filter_by(user_id=user_id, roadmap_id=roadmap_id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=404,
            detail="No preferences found for this user/roadmap combination.",
        )

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record

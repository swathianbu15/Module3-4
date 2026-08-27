"""
Database connection setup for Module 3 & Module 4.

Uses PostgreSQL via SQLAlchemy. Connection string is read from the
DATABASE_URL environment variable so it can be swapped for the team's
shared database later without touching any other code.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Example: postgresql://user:password@localhost:5432/training_platform
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./dev.db",
)

# Convert postgresql:// to postgresql+psycopg:// if psycopg v3 is installed and +psycopg is not explicitly set
if DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+"):
    try:
        import psycopg  # noqa: F401
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    except ImportError:
        pass

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session and
    guarantees it's closed after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

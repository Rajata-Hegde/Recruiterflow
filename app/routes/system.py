import sqlite3
from fastapi import APIRouter, Depends
from app.database import get_db, init_db, seed_db, fetch_all_candidates, fetch_all_jobs
from app.models import MessageResponse

router = APIRouter(prefix="", tags=["System"])


@router.get("/health", summary="Health Check")
def health_check(conn: sqlite3.Connection = Depends(get_db)):
    """Health check endpoint verifying application and database connectivity."""
    candidates_count = len(fetch_all_candidates(conn))
    jobs_count = len(fetch_all_jobs(conn))
    return {
        "status": "healthy",
        "service": "RecruiterFlow Recruiter Bot",
        "database": "SQLite (Raw SQL)",
        "total_candidates": candidates_count,
        "total_jobs": jobs_count
    }


@router.post("/api/seed", response_model=MessageResponse, summary="Seed Database")
def seed_database():
    """Seeds the database with candidate profiles and job openings from seed.sql."""
    init_db()
    seed_db()
    return MessageResponse(message="Database successfully seeded with candidates and jobs.")


@router.post("/api/reset", response_model=MessageResponse, summary="Reset Database")
def reset_database():
    """Resets database schema to an empty state using ddl.sql."""
    init_db()
    return MessageResponse(message="Database successfully reset to empty schema.")

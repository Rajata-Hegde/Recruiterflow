import sqlite3
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import (
    get_db,
    fetch_all_jobs,
    fetch_job_by_id,
    insert_job,
    fetch_all_candidates,
    log_match_history
)
from app.models import (
    JobResponse,
    JobCreate,
    JobMatchesResponse
)
from app.matcher import rank_candidates_for_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=List[JobResponse], summary="List all jobs")
def list_jobs(conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve all open job postings with required skills and culture keywords."""
    return fetch_all_jobs(conn)


@router.get("/{job_id}", response_model=JobResponse, summary="Get job by ID")
def get_job(job_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve a single job posting by ID."""
    job = fetch_job_by_id(conn, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )
    return job


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED, summary="Ingest job opening")
def create_job(payload: JobCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Ingest a new job opening into the database using raw SQL."""
    job_id = insert_job(
        conn=conn,
        title=payload.title,
        min_experience=payload.min_experience,
        tagline=payload.tagline,
        required_skills=payload.required_skills,
        culture_keywords=payload.culture_keywords
    )
    created_job = fetch_job_by_id(conn, job_id)
    return created_job


@router.get("/{job_id}/matches", response_model=JobMatchesResponse, summary="Ranked candidates for a job")
def get_job_matches(job_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """
    Core matching endpoint:
    Ranks all ingested candidate profiles for the given job opening.
    Returns:
    - 0-100 overall score
    - Dimensional score breakdown (Skills 50%, Experience 25%, Culture 15%, Availability 10%)
    - Character-aware explanation and quirk insight
    - Exact matched & missing skills
    """
    job = fetch_job_by_id(conn, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    all_candidates = fetch_all_candidates(conn)
    matches = rank_candidates_for_job(all_candidates, job)

    # Optionally persist top matches into match_history log table safely
    try:
        for match in matches[:5]:
            candidate_id = match["candidate"]["id"]
            log_match_history(
                conn=conn,
                job_id=job_id,
                candidate_id=candidate_id,
                score=match["score"],
                reason=match["reason"]
            )
    except Exception:
        # Non-critical audit logging should never fail the GET query response
        pass

    return JobMatchesResponse(
        job=JobResponse(**job),
        total_candidates_evaluated=len(all_candidates),
        matches=matches
    )


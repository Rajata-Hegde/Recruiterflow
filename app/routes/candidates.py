import sqlite3
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import (
    get_db,
    fetch_all_candidates,
    fetch_candidate_by_id,
    insert_candidate,
    fetch_all_jobs
)
from app.models import (
    CandidateResponse,
    CandidateCreate,
    CandidateMatchesResponse
)
from app.matcher import rank_jobs_for_candidate

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("", response_model=List[CandidateResponse], summary="List all candidates")
def list_candidates(conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve all ingested candidate profiles along with their skills and traits."""
    return fetch_all_candidates(conn)


@router.get("/{candidate_id}", response_model=CandidateResponse, summary="Get candidate by ID")
def get_candidate(candidate_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve a single candidate profile by ID."""
    candidate = fetch_candidate_by_id(conn, candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found."
        )
    return candidate


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED, summary="Ingest candidate profile")
def create_candidate(payload: CandidateCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Ingest a new candidate profile into the database using raw SQL."""
    candidate_id = insert_candidate(
        conn=conn,
        name=payload.name,
        experience_years=payload.experience_years,
        availability=payload.availability,
        quirk=payload.quirk,
        skills=payload.skills,
        traits=payload.traits
    )
    created_candidate = fetch_candidate_by_id(conn, candidate_id)
    return created_candidate


@router.get("/{candidate_id}/matches", response_model=CandidateMatchesResponse, summary="Ranked jobs for a candidate")
def get_candidate_matches(candidate_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """
    Reverse matching endpoint:
    Ranks all open job openings for the given candidate profile, returning
    match scores (0-100), dimensional score breakdowns, and human-readable reasons.
    """
    candidate = fetch_candidate_by_id(conn, candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found."
        )

    all_jobs = fetch_all_jobs(conn)
    matches = rank_jobs_for_candidate(candidate, all_jobs)

    return CandidateMatchesResponse(
        candidate=CandidateResponse(**candidate),
        total_jobs_evaluated=len(all_jobs),
        matches=matches
    )

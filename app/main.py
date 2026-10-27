"""
RecruiterFlow - Recruiter Bot Backend Service.
Prototype matching engine for ranking candidates and jobs.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, seed_db, get_db_connection, fetch_all_candidates
from app.routes import candidates, jobs, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to ensure database schema and seed data exist."""
    init_db()
    conn = get_db_connection()
    try:
        existing_candidates = fetch_all_candidates(conn)
        if not existing_candidates:
            # Auto-seed initial fictional dataset if database is empty
            seed_db()
    finally:
        conn.close()
    yield


app = FastAPI(
    title="RecruiterFlow Recruiter Bot API",
    description=(
        "A specialized backend matching engine that ingests candidate profiles and job openings, "
        "then ranks the best matches using a multi-factor weighted scoring model (Skills, Experience, "
        "Culture, and Availability) with character-aware explainability. "
        "Powered entirely by pure raw SQL."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local testing or web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(system.router)
app.include_router(candidates.router)
app.include_router(jobs.router)


@app.get("/", summary="Root Index")
def root_index():
    return {
        "service": "RecruiterFlow Recruiter Bot",
        "documentation": "/docs",
        "endpoints": {
            "list_jobs": "GET /jobs",
            "job_matches": "GET /jobs/{id}/matches",
            "list_candidates": "GET /candidates",
            "candidate_matches": "GET /candidates/{id}/matches",
            "health_check": "GET /health",
            "seed_data": "POST /api/seed"
        }
    }

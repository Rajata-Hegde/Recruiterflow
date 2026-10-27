import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, seed_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure database is initialized and seeded before tests run."""
    init_db()
    seed_db()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_root_index(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "documentation" in data
    assert data["service"] == "RecruiterFlow Recruiter Bot"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["total_candidates"] == 15
    assert data["total_jobs"] == 6


def test_list_jobs(client):
    response = client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) >= 6
    titles = [j["title"] for j in jobs]
    assert "Backend Detective" in titles
    assert "Rapid Prototyping Engineer" in titles


def test_get_single_job(client):
    response = client.get("/jobs/1")
    assert response.status_code == 200
    job = response.json()
    assert job["id"] == 1
    assert job["title"] == "Backend Detective"
    assert "deduction" in job["required_skills"]
    assert "forensics" in job["required_skills"]


def test_get_nonexistent_job(client):
    response = client.get("/jobs/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_candidates(client):
    response = client.get("/candidates")
    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) >= 15
    names = [c["name"] for c in candidates]
    assert "Sherlock H." in names
    assert "Michael Scott" not in names  # In seed data it's Michael S.
    assert "Michael S." in names


def test_get_single_candidate(client):
    response = client.get("/candidates/1")
    assert response.status_code == 200
    cand = response.json()
    assert cand["id"] == 1
    assert cand["name"] == "Sherlock H."
    assert cand["experience_years"] == 8
    assert "deduction" in cand["skills"]


def test_job_matches_core_requirement(client):
    """
    Test GET /jobs/{id}/matches:
    Verifies that candidates are ranked with a score, short reason, and breakdown.
    For Job 1 (Backend Detective), Sherlock Holmes should rank #1.
    """
    response = client.get("/jobs/1/matches")
    assert response.status_code == 200
    data = response.json()

    assert data["job"]["id"] == 1
    assert data["total_candidates_evaluated"] >= 15
    matches = data["matches"]
    assert len(matches) > 0

    # Top ranked candidate must be Sherlock Holmes
    top_match = matches[0]
    assert top_match["rank"] == 1
    assert top_match["candidate"]["name"] == "Sherlock H."
    assert top_match["score"] > 85.0
    assert "reason" in top_match
    assert len(top_match["reason"]) > 10
    assert "deduction" in top_match["matched_skills"]
    assert top_match["breakdown"]["skills_score"] == 45.0


def test_candidate_matches_reverse_requirement(client):
    """
    Test GET /candidates/{id}/matches:
    Verifies reverse matching of jobs for a candidate.
    For Sherlock Holmes (Candidate 1), Backend Detective should rank #1.
    """
    response = client.get("/candidates/1/matches")
    assert response.status_code == 200
    data = response.json()

    assert data["candidate"]["id"] == 1
    assert data["total_jobs_evaluated"] >= 6
    matches = data["matches"]
    assert len(matches) > 0

    top_match = matches[0]
    assert top_match["rank"] == 1
    assert top_match["job"]["title"] == "Backend Detective"
    assert top_match["score"] > 85.0
    assert "reason" in top_match


def test_ingest_candidate_and_job(client):
    """Test manual ingestion of a new candidate and new job."""
    # Ingest candidate
    new_candidate = {
        "name": "Benoit Blanc",
        "experience_years": 14,
        "availability": "Immediate",
        "quirk": "Speaks in elaborate donut metaphors.",
        "skills": ["deduction", "forensics", "observation"],
        "traits": ["analytical", "eccentric"]
    }
    cand_resp = client.post("/candidates", json=new_candidate)
    assert cand_resp.status_code == 201
    cand_data = cand_resp.json()
    new_cand_id = cand_data["id"]
    assert cand_data["name"] == "Benoit Blanc"

    # Ingest job
    new_job = {
        "title": "Lead Mystery Investigator",
        "min_experience": 5,
        "tagline": "The donut hole inside the donut.",
        "required_skills": ["deduction", "observation"],
        "culture_keywords": ["analytical"]
    }
    job_resp = client.post("/jobs", json=new_job)
    assert job_resp.status_code == 201
    job_data = job_resp.json()
    new_job_id = job_data["id"]

    # Test matching newly ingested candidate against new job
    match_resp = client.get(f"/jobs/{new_job_id}/matches")
    assert match_resp.status_code == 200
    matches = match_resp.json()["matches"]
    top_cand = matches[0]
    assert top_cand["candidate"]["name"] == "Benoit Blanc"
    assert top_cand["rank"] == 1

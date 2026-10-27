import pytest
from app.matcher import calculate_match_details, rank_candidates_for_job, rank_jobs_for_candidate


def test_perfect_skill_and_experience_match():
    candidate = {
        "id": 1,
        "name": "Sherlock H.",
        "experience_years": 8,
        "availability": "Immediate",
        "quirk": "Solves problems by eliminating the impossible; occasionally insufferable in standups.",
        "skills": ["deduction", "pattern-recognition", "forensics"],
        "traits": ["analytical", "blunt"]
    }
    job = {
        "id": 1,
        "title": "Backend Detective",
        "min_experience": 3,
        "tagline": "We have a bug. We have no leads. We have you.",
        "required_skills": ["deduction", "pattern-recognition", "forensics"],
        "culture_keywords": ["analytical", "autonomous"]
    }

    details = calculate_match_details(candidate, job)
    assert details["score"] > 85.0
    assert details["skills_score"] == 45.0
    assert details["experience_score"] > 20.0  # meets min 3 and has seniority bonus
    assert details["availability_score"] == 10.0
    assert "deduction" in details["matched_skills"]
    assert "forensics" in details["matched_skills"]
    assert "pattern-recognition" in details["matched_skills"]
    assert "analytical" in details["matched_traits"]
    assert "Perfect skill match" in details["reason"]
    assert "Quirk heads-up:" in details["reason"]


def test_underqualified_experience_penalty():
    junior_candidate = {
        "id": 99,
        "name": "Junior Dev",
        "experience_years": 1,
        "availability": "Immediate",
        "quirk": "Always tests in prod.",
        "skills": ["deduction", "pattern-recognition", "forensics"],
        "traits": ["analytical"]
    }
    senior_job = {
        "id": 1,
        "title": "Backend Detective",
        "min_experience": 5,
        "tagline": "Senior level only",
        "required_skills": ["deduction", "pattern-recognition", "forensics"],
        "culture_keywords": ["analytical"]
    }

    details = calculate_match_details(junior_candidate, senior_job)
    # 1 / 5 * 15.0 = 3.0
    assert details["experience_score"] == pytest.approx(3.0, 0.1)
    assert "falls short of min 5 yrs" in details["reason"]


def test_availability_weights():
    cand_immediate = {
        "id": 1, "name": "A", "experience_years": 5, "availability": "Immediate",
        "skills": ["rapid-prototyping"], "traits": ["calm"]
    }
    cand_passive = {
        "id": 2, "name": "B", "experience_years": 5, "availability": "Not looking",
        "skills": ["rapid-prototyping"], "traits": ["calm"]
    }
    job = {
        "id": 1, "title": "Job", "min_experience": 5,
        "required_skills": ["rapid-prototyping"], "culture_keywords": ["calm"]
    }

    details_imm = calculate_match_details(cand_immediate, job)
    details_pas = calculate_match_details(cand_passive, job)

    assert details_imm["availability_score"] == 10.0
    assert details_pas["availability_score"] == 2.0
    assert details_imm["score"] > details_pas["score"]


def test_ranking_candidates_for_job():
    job = {
        "id": 1,
        "title": "Backend Detective",
        "min_experience": 3,
        "required_skills": ["deduction", "pattern-recognition", "forensics"],
        "culture_keywords": ["analytical", "autonomous"]
    }
    candidates = [
        {
            "id": 1,
            "name": "Sherlock H.",
            "experience_years": 8,
            "availability": "Immediate",
            "quirk": "Eliminating impossible.",
            "skills": ["deduction", "pattern-recognition", "forensics"],
            "traits": ["analytical", "blunt"]
        },
        {
            "id": 5,
            "name": "Ron S.",
            "experience_years": 15,
            "availability": "Not looking",
            "quirk": "One monitor only.",
            "skills": ["woodworking", "minimalism", "negotiation"],
            "traits": ["stubborn", "principled"]
        }
    ]

    ranked = rank_candidates_for_job(candidates, job)
    assert ranked[0]["candidate"]["name"] == "Sherlock H."
    assert ranked[0]["rank"] == 1
    assert ranked[1]["candidate"]["name"] == "Ron S."
    assert ranked[1]["rank"] == 2


def test_reverse_matching_for_candidate():
    candidate = {
        "id": 1,
        "name": "Sherlock H.",
        "experience_years": 8,
        "availability": "Immediate",
        "quirk": "Eliminating impossible.",
        "skills": ["deduction", "pattern-recognition", "forensics"],
        "traits": ["analytical", "blunt"]
    }
    jobs = [
        {
            "id": 1,
            "title": "Backend Detective",
            "min_experience": 3,
            "required_skills": ["deduction", "pattern-recognition", "forensics"],
            "culture_keywords": ["analytical", "autonomous"]
        },
        {
            "id": 6,
            "title": "Sales Engineer",
            "min_experience": 3,
            "required_skills": ["sales", "public-speaking", "negotiation"],
            "culture_keywords": ["enthusiastic", "persistent"]
        }
    ]

    ranked = rank_jobs_for_candidate(candidate, jobs)
    assert ranked[0]["job"]["title"] == "Backend Detective"
    assert ranked[0]["rank"] == 1
    assert ranked[0]["score"] > ranked[1]["score"]

"""
Matching Engine for RecruiterFlow Recruiter Bot.
Implements the multi-factor scoring model:
- Skill overlap & breadth (50%)
- Experience fit & seniority (25%)
- Trait & culture synergy (15%)
- Availability & hiring readiness (10%)
Includes character-aware explainability and tie-breaking.
"""

from typing import List, Dict, Any, Tuple, Set


# Semantic trait affinity clusters for culture fit scoring
TRAIT_SYNONYMS: Dict[str, Set[str]] = {
    "analytical": {"analytical", "detail-oriented", "rigid", "brilliant", "sharp", "forensics"},
    "autonomous": {"autonomous", "principled", "stubborn", "blunt", "confident", "decisive"},
    "innovative": {"innovative", "genius", "confident", "improviser", "resourceful", "sharp"},
    "fast-paced": {"fast-paced", "reckless", "improviser", "calm", "rapid-prototyping"},
    "energetic": {"energetic", "optimistic", "enthusiastic", "overachiever", "sharp"},
    "curious": {"curious", "research", "detail-oriented", "brilliant", "theoretical-analysis"},
    "empathetic": {"empathetic", "mentorship", "optimism", "calm", "loyalty"},
    "organized": {"organized", "tenacious", "detail-oriented", "time-management", "precision"},
    "decisive": {"decisive", "demanding", "intense", "resilient", "leadership"},
    "calm-under-pressure": {"calm-under-pressure", "calm", "resilient", "crisis-management", "improviser"},
    "enthusiastic": {"enthusiastic", "optimistic", "chaotic", "persistent", "tenacious"},
    "persistent": {"persistent", "tenacious", "stubborn", "loyal", "resilient"}
}

# Availability score mapping (out of 10 points)
AVAILABILITY_SCORES: Dict[str, float] = {
    "Immediate": 10.0,
    "2 weeks": 7.5,
    "Not looking": 2.0
}


def calculate_match_details(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes score breakdown and human-readable explanation for a candidate and job pair.
    
    Returns:
        dict containing:
            - total_score (float, 0-100)
            - skills_score (float, 0-50)
            - experience_score (float, 0-25)
            - culture_score (float, 0-15)
            - availability_score (float, 0-10)
            - matched_skills (list of str)
            - missing_skills (list of str)
            - matched_traits (list of str)
            - reason (str)
    """
    candidate_skills = {s.strip().lower() for s in candidate.get("skills", [])}
    candidate_traits = {t.strip().lower() for t in candidate.get("traits", [])}
    job_required_skills = {s.strip().lower() for s in job.get("required_skills", [])}
    job_culture = {k.strip().lower() for k in job.get("culture_keywords", [])}

    # -------------------------------------------------------------------------
    # 1. Skill Fit Score (Max 50 points)
    # -------------------------------------------------------------------------
    matched_skills_set = candidate_skills & job_required_skills
    missing_skills_set = job_required_skills - candidate_skills
    matched_skills = sorted(list(matched_skills_set))
    missing_skills = sorted(list(missing_skills_set))

    total_req_count = len(job_required_skills) if job_required_skills else 1
    overlap_ratio = len(matched_skills_set) / total_req_count
    base_skill_score = overlap_ratio * 45.0

    # Breadth bonus: candidate has additional domain skills beyond required
    extra_skills = candidate_skills - job_required_skills
    # If candidate matches at least 1 required skill, award breadth bonus up to 5 pts
    if matched_skills_set:
        breadth_bonus = min(5.0, len(extra_skills) * 1.0)
    else:
        # Zero required skills matched -> breadth bonus is heavily capped
        breadth_bonus = 0.0

    skills_score = round(min(50.0, base_skill_score + breadth_bonus), 2)

    # -------------------------------------------------------------------------
    # 2. Experience Fit Score (Max 25 points)
    # -------------------------------------------------------------------------
    cand_exp = candidate.get("experience_years", 0)
    min_exp = job.get("min_experience", 0)

    if cand_exp >= min_exp:
        # Candidate meets or exceeds minimum requirement
        base_exp_score = 20.0
        # Seniority bonus: 1 pt per 2 excess years, capped at 5 pts
        excess_years = cand_exp - min_exp
        seniority_bonus = min(5.0, excess_years * 0.5)
        experience_score = round(base_exp_score + seniority_bonus, 2)
        exp_reason_part = f"{cand_exp} yrs exp meets min {min_exp} yrs"
        if excess_years > 0:
            exp_reason_part += f" (+{excess_years} yrs seniority bonus)"
    else:
        # Underqualified experience gap penalty
        exp_ratio = (cand_exp / min_exp) if min_exp > 0 else 0
        experience_score = round(exp_ratio * 15.0, 2)
        exp_reason_part = f"{cand_exp} yrs exp falls short of min {min_exp} yrs"

    # -------------------------------------------------------------------------
    # 3. Culture & Trait Alignment Score (Max 15 points)
    # -------------------------------------------------------------------------
    direct_traits = candidate_traits & job_culture
    matched_traits_set = set(direct_traits)
    semantic_matches = set()

    # Check semantic affinity for remaining culture keywords
    unmatched_culture = job_culture - direct_traits
    for kw in unmatched_culture:
        synonyms = TRAIT_SYNONYMS.get(kw, set())
        overlap = candidate_traits & synonyms
        if overlap:
            matched_traits_set.add(f"{list(overlap)[0]}~{kw}")
            semantic_matches.add(kw)

    direct_points = len(direct_traits) * 7.5
    semantic_points = len(semantic_matches) * 3.75
    culture_score = round(min(15.0, direct_points + semantic_points), 2)

    matched_traits = sorted(list(matched_traits_set))

    # -------------------------------------------------------------------------
    # 4. Availability Score (Max 10 points)
    # -------------------------------------------------------------------------
    avail_status = candidate.get("availability", "Not looking")
    availability_score = AVAILABILITY_SCORES.get(avail_status, 2.0)

    # -------------------------------------------------------------------------
    # Total Score Computation (0 - 100)
    # -------------------------------------------------------------------------
    total_score = round(skills_score + experience_score + culture_score + availability_score, 1)

    # -------------------------------------------------------------------------
    # Character-Aware Reason Generation
    # -------------------------------------------------------------------------
    reason_parts = []
    
    # Skills summary
    if len(matched_skills) == total_req_count:
        reason_parts.append(f"Perfect skill match ({len(matched_skills)}/{total_req_count}: {', '.join(matched_skills)})")
    elif len(matched_skills) > 0:
        reason_parts.append(f"Partial skill match ({len(matched_skills)}/{total_req_count}: {', '.join(matched_skills)}; missing: {', '.join(missing_skills)})")
    else:
        reason_parts.append(f"No direct skill overlap (missing: {', '.join(missing_skills)})")

    # Experience summary
    reason_parts.append(exp_reason_part)

    # Culture summary
    if direct_traits:
        reason_parts.append(f"Culture synergy on '{', '.join(sorted(direct_traits))}'")
    elif semantic_matches:
        reason_parts.append(f"Adjacent culture traits aligned with '{', '.join(sorted(semantic_matches))}'")

    # Availability summary
    if avail_status == "Immediate":
        reason_parts.append("Available immediately")
    elif avail_status == "2 weeks":
        reason_parts.append("Standard 2-week notice period")
    else:
        reason_parts.append("Currently passive / not looking")

    # Character Quirk
    quirk = candidate.get("quirk")
    if quirk:
        reason_parts.append(f"Quirk heads-up: \"{quirk}\"")

    full_reason = ". ".join(reason_parts) + "."

    return {
        "score": total_score,
        "skills_score": skills_score,
        "experience_score": experience_score,
        "culture_score": culture_score,
        "availability_score": availability_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_traits": matched_traits,
        "reason": full_reason
    }


def rank_candidates_for_job(candidates: List[Dict[str, Any]], job: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ranks a list of candidate profiles against a single job opening.
    Applies tie-breaking:
    1. Overall score (descending)
    2. Skills score (descending)
    3. Experience years (descending)
    4. Candidate ID (ascending)
    """
    evaluated = []
    for candidate in candidates:
        details = calculate_match_details(candidate, job)
        evaluated.append({
            "candidate": candidate,
            "score": details["score"],
            "reason": details["reason"],
            "breakdown": {
                "skills_score": details["skills_score"],
                "experience_score": details["experience_score"],
                "culture_score": details["culture_score"],
                "availability_score": details["availability_score"],
            },
            "matched_skills": details["matched_skills"],
            "missing_skills": details["missing_skills"],
            "matched_traits": details["matched_traits"],
            "_tie_breaker": (
                -details["score"],
                -details["skills_score"],
                -candidate.get("experience_years", 0),
                candidate.get("id", 0)
            )
        })

    # Sort with deterministic tie-breaking
    evaluated.sort(key=lambda item: item["_tie_breaker"])

    # Assign rank (1-indexed)
    for index, item in enumerate(evaluated, start=1):
        item["rank"] = index
        del item["_tie_breaker"]

    return evaluated


def rank_jobs_for_candidate(candidate: Dict[str, Any], jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ranks a list of job openings for a single candidate profile (reverse direction).
    Applies tie-breaking:
    1. Overall score (descending)
    2. Skills score (descending)
    3. Job ID (ascending)
    """
    evaluated = []
    for job in jobs:
        details = calculate_match_details(candidate, job)
        evaluated.append({
            "job": job,
            "score": details["score"],
            "reason": details["reason"],
            "breakdown": {
                "skills_score": details["skills_score"],
                "experience_score": details["experience_score"],
                "culture_score": details["culture_score"],
                "availability_score": details["availability_score"],
            },
            "matched_skills": details["matched_skills"],
            "missing_skills": details["missing_skills"],
            "matched_traits": details["matched_traits"],
            "_tie_breaker": (
                -details["score"],
                -details["skills_score"],
                job.get("id", 0)
            )
        })

    # Sort with deterministic tie-breaking
    evaluated.sort(key=lambda item: item["_tie_breaker"])

    for index, item in enumerate(evaluated, start=1):
        item["rank"] = index
        del item["_tie_breaker"]

    return evaluated

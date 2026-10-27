from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


# -----------------------------------------------------------------------------
# Candidate Schemas
# -----------------------------------------------------------------------------

class CandidateBase(BaseModel):
    name: str = Field(..., examples=["Sherlock H."])
    experience_years: int = Field(..., ge=0, examples=[8])
    availability: Literal["Immediate", "2 weeks", "Not looking"] = Field(..., examples=["Immediate"])
    quirk: str = Field(..., examples=["Solves problems by eliminating the impossible; occasionally insufferable in standups."])
    skills: List[str] = Field(default_factory=list, examples=[["deduction", "pattern-recognition", "forensics"]])
    traits: List[str] = Field(default_factory=list, examples=[["analytical", "blunt"]])


class CandidateCreate(CandidateBase):
    pass


class CandidateResponse(CandidateBase):
    id: int
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Job Schemas
# -----------------------------------------------------------------------------

class JobBase(BaseModel):
    title: str = Field(..., examples=["Backend Detective"])
    min_experience: int = Field(..., ge=0, examples=[3])
    tagline: str = Field(..., examples=["We have a bug. We have no leads. We have you."])
    required_skills: List[str] = Field(default_factory=list, examples=[["deduction", "pattern-recognition", "forensics"]])
    culture_keywords: List[str] = Field(default_factory=list, examples=[["analytical", "autonomous"]])


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Matching & Scoring Schemas
# -----------------------------------------------------------------------------

class ScoreBreakdown(BaseModel):
    skills_score: float = Field(..., description="Skill overlap and breadth score (0 - 50 pts)")
    experience_score: float = Field(..., description="Experience alignment and seniority score (0 - 25 pts)")
    culture_score: float = Field(..., description="Culture keyword and trait synergy score (0 - 15 pts)")
    availability_score: float = Field(..., description="Candidate readiness and availability score (0 - 10 pts)")


class CandidateMatchItem(BaseModel):
    rank: int = Field(..., description="Rank among all evaluated candidates")
    candidate: CandidateResponse
    score: float = Field(..., description="Overall weighted match score (0 - 100)")
    reason: str = Field(..., description="Human-readable recruiter explanation with personality insight")
    breakdown: ScoreBreakdown
    matched_skills: List[str]
    missing_skills: List[str]
    matched_traits: List[str]


class JobMatchesResponse(BaseModel):
    job: JobResponse
    total_candidates_evaluated: int
    matches: List[CandidateMatchItem]


class JobMatchItem(BaseModel):
    rank: int = Field(..., description="Rank among all open jobs for this candidate")
    job: JobResponse
    score: float = Field(..., description="Overall weighted match score (0 - 100)")
    reason: str = Field(..., description="Human-readable candidate fit explanation with personality insight")
    breakdown: ScoreBreakdown
    matched_skills: List[str]
    missing_skills: List[str]
    matched_traits: List[str]


class CandidateMatchesResponse(BaseModel):
    candidate: CandidateResponse
    total_jobs_evaluated: int
    matches: List[JobMatchItem]


# -----------------------------------------------------------------------------
# System & General Schemas
# -----------------------------------------------------------------------------

class MessageResponse(BaseModel):
    message: str
    status: str = "success"

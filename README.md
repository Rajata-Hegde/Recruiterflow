# RecruiterFlow — Recruiter Bot & SQL Detective Challenge

A high-performance backend prototype for **Recruiter Bot** that ingests candidate profiles and job openings, then computes and ranks the best matches using a multi-factor weighted scoring model with personality-aware explainability.

Built with **Python 3.10+**, **FastAPI**, and **pure hand-written raw SQL** (zero ORMs, zero query builders) backed by **SQLite**.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Quickstart & Local Installation](#quickstart--local-installation)
3. [Architecture & Database Schema](#architecture--database-schema)
4. [The Matching Algorithm: Decisions & Trade-Offs](#the-matching-algorithm-decisions--trade-offs)
5. [API Reference & cURL Examples](#api-reference--curl-examples)
6. [Part 2: The SQL Detective Challenge](#part-2-the-sql-detective-challenge)
7. [Automated Testing](#automated-testing)
8. [AI Tools Disclosure](#ai-tools-disclosure)

---

## Project Overview

Recruiter Bot evaluates candidates against open job requisitions. To make building and grading fun, our dataset features iconic fictional characters (from Sherlock Holmes and Hermione Granger to Rick Sanchez and Michael Scott).

Key Deliverables:
- **Part 1 — Recruiter Bot Core Service**:
  - Ingestion endpoints & raw SQL seeding script.
  - Normalized relational database schema in pure raw SQL.
  - Core endpoint: `GET /jobs/{id}/matches` (ranked candidates with score and reason).
  - Reverse endpoint: `GET /candidates/{id}/matches` (ranked jobs for a candidate).
  - Interactive Swagger API docs at `http://localhost:8000/docs`.
- **Part 2 — The SQL Detective Challenge**:
  - `sql_detective.sql` answering all 5 hiring-ops questions.
  - `run_sql_detective.py` automated runner & verifier script.

---

## Quickstart & Local Installation

### Prerequisites
- Python 3.10+
- `pip`

### 1. Clone & Set Up Environment
```bash
git clone <your-repo-url>
cd recruiterflow

# (Optional) Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Seed the Database
Initialize tables from `app/ddl.sql` and load seed candidates and jobs from `app/seed.sql`:
```bash
python seed.py
```

### 3. Run the API Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: **[http://localhost:8000/docs](http://localhost:8000/docs)**
- Alternative ReDoc UI: **[http://localhost:8000/redoc](http://localhost:8000/redoc)**
- Health Check: **[http://localhost:8000/health](http://localhost:8000/health)**

### 4. Run the Terminal Demo (Optional)
To see instant ranking results for all jobs and candidates in formatted terminal tables:
```bash
python demo.py
```

---

## Architecture & Database Schema

Per project requirements, **no ORMs or query builders are used anywhere**. Every schema definition, data mutation, and query is pure hand-written parameterized SQL.

```
recruiterflow/
├── app/
│   ├── ddl.sql               # Hand-written DDL statements & indexes
│   ├── seed.sql              # Hand-written seed data SQL script
│   ├── config.py             # System paths and configuration
│   ├── database.py           # Pure raw SQL database driver & queries
│   ├── models.py             # Pydantic v2 schemas for API validation & OpenAPI docs
│   ├── matcher.py            # Recruiter Bot multi-factor matching engine
│   ├── main.py               # FastAPI application setup & lifespan hooks
│   └── routes/
│       ├── candidates.py     # Candidate ingestion & reverse matching routes
│       ├── jobs.py           # Job ingestion & core matching routes
│       └── system.py         # Health and DB management routes
├── tests/
│   ├── test_matcher.py       # Unit tests for scoring weights, quirks, & tie-breaking
│   ├── test_api.py           # Integration tests for all HTTP API endpoints
│   └── test_sql_detective.py # Automated tests for Part 2 queries
├── sql_detective.sql         # Part 2 SQL Detective queries with full commentary
├── run_sql_detective.py      # Executable verifier script for Part 2
├── seed.py                   # Standalone database seeder CLI
├── demo.py                   # Pretty terminal demo runner
├── requirements.txt          # Production and testing dependencies
└── README.md                 # Project documentation
```

### Normalized Database Schema (`app/ddl.sql`)

```
   +------------------+         +---------------------+
   |    candidates    | 1     N |   candidate_skills  |
   |------------------|<------->|---------------------|
   | id (PK)          |         | candidate_id (FK)   |
   | name             |         | skill (PK)          |
   | experience_years |         +---------------------+
   | availability     |         +---------------------+
   | quirk            | 1     N |   candidate_traits  |
   +------------------|<------->|---------------------|
                                | candidate_id (FK)   |
                                | trait (PK)          |
                                +---------------------+

   +------------------+         +---------------------+
   |       jobs       | 1     N |      job_skills     |
   |------------------|<------->|---------------------|
   | id (PK)          |         | job_id (FK)         |
   | title            |         | skill (PK)          |
   | min_experience   |         +---------------------+
   | tagline          |         +---------------------+
   +------------------| 1     N | job_culture_keywords|
                      |<------->|---------------------|
                                | job_id (FK)         |
                                | keyword (PK)        |
                                +---------------------+
```

- **1NF to 3NF Normalized Structure**: Candidate skills, candidate traits, job skills, and culture keywords are split into dedicated relation tables with foreign keys (`ON DELETE CASCADE`).
- **Data Integrity**: Enforced SQLite constraints (`CHECK (experience_years >= 0)`, `CHECK (availability IN (...))`, foreign key pragma).
- **Relational Performance**: B-tree indexes added on `skill`, `trait`, `keyword`, and experience columns.

---

## The Matching Algorithm: Decisions & Trade-Offs

The matching engine in `app/matcher.py` evaluates candidates and jobs across **4 core dimensions**, normalizing output to a **0 – 100 point scale**:

$$\text{Total Score} = \text{Skills (0–50)} + \text{Experience (0–25)} + \text{Culture \& Traits (0–15)} + \text{Availability (0–10)}$$

### 1. Skill Fit Score (50% Weight, 0 – 50 pts)
*Why 50%?* In technical recruitment, required skills are hard qualifiers. A candidate lacking core domain skills cannot perform the duties regardless of availability.
- **Required Skill Overlap**: $\text{Overlap Ratio} = \frac{|\text{Candidate Skills} \cap \text{Job Required Skills}|}{|\text{Job Required Skills}|}$. Scales up to 45.0 points.
- **Complementary Breadth Bonus**: Up to +5.0 points for adjacent domain skills (e.g., Rick Sanchez bringing `chemistry` to Systems Engineering, or MacGyver bringing `resourcefulness`). If a candidate has zero required skills, breadth bonus is capped at 0.

### 2. Experience Fit Score (25% Weight, 0 – 25 pts)
- **Qualified Candidates ($E_c \ge E_{min}$)**:
  - Base qualification: 20.0 points.
  - Seniority Bonus: +1.0 point per 2 excess years above minimum, capped at +5.0 points (max 25.0 points).
- **Underqualified Candidates ($E_c < E_{min}$)**:
  - Proportional gap scaling: $\left(\frac{E_c}{E_{min}}\right) \times 15.0$ points (cannot clear 15.0).
- *Trade-off / Seniority Handling*: We intentionally avoid arbitrarily penalizing high-seniority candidates (e.g. Rick Sanchez with 20 yrs for a 2-yr role). In technical staffing, having deep experience is an asset, but we flag role-scope verification in the explanation reason.

### 3. Culture & Trait Synergy (15% Weight, 0 – 15 pts)
- **Direct Keyword Matches**: Exact match between candidate traits and job culture keywords (e.g., Sherlock Holmes' `analytical` trait matching Backend Detective's `analytical` culture) awards 7.5 points each.
- **Semantic / Synonym Clusters**: Recognizes adjacent traits using curated affinity clusters (e.g., `fast-paced` synergizes with `reckless`, `improviser`, and `rapid-prototyping`; `organized` synergizes with `tenacious` and `detail-oriented`). Awards 3.75 points per adjacent alignment.

### 4. Availability & Sourcing Readiness (10% Weight, 0 – 10 pts)
Reflects hiring feasibility and velocity:
- **Immediate**: 10.0 pts (Candidate is active and ready to sign today).
- **2 weeks**: 7.5 pts (Employed, standard low-risk notice period).
- **Not looking**: 2.0 pts (Passive candidate; requires heavy outreach and headhunting).

*Case Study*: For **Rapid Prototyping Engineer**, both Tony Stark and Rick Sanchez have 100% skill overlap. However, Rick Sanchez (Immediate) scores **88.5** while Tony Stark (Not looking) scores **80.5**. This accurately reflects recruitment reality: passive candidates require higher recruiting friction and risk.

### 5. Deterministic Tie-Breaking
When candidates achieve identical scores:
1. Higher `skills_score` (technical qualification first)
2. Higher `experience_years`
3. Lower candidate ID (deterministic FIFO)

### 6. Explainability & Character Quirk Synthesis
Recruiters must never receive unexplained scores. Every match output includes:
- Categorical breakdown (`skills_score`, `experience_score`, `culture_score`, `availability_score`)
- Lists of `matched_skills` and `missing_skills`
- A human-readable synthesis incorporating the candidate's quirk (e.g. `"Perfect 3/3 skill match... Culture synergy on 'analytical'. Available immediately. Quirk heads-up: Solves problems by eliminating the impossible; occasionally insufferable in standups."`).

---

## API Reference & cURL Examples

### 1. Ranked Candidates for a Job (Core Project Endpoint)
`GET /jobs/{id}/matches`

```bash
curl -X GET "http://localhost:8000/jobs/1/matches" -H "Accept: application/json"
```

**Example JSON Response:**
```json
{
  "job": {
    "id": 1,
    "title": "Backend Detective",
    "min_experience": 3,
    "tagline": "We have a bug. We have no leads. We have you.",
    "required_skills": ["deduction", "forensics", "pattern-recognition"],
    "culture_keywords": ["analytical", "autonomous"]
  },
  "total_candidates_evaluated": 15,
  "matches": [
    {
      "rank": 1,
      "candidate": {
        "id": 1,
        "name": "Sherlock H.",
        "experience_years": 8,
        "availability": "Immediate",
        "quirk": "Solves problems by eliminating the impossible; occasionally insufferable in standups.",
        "skills": ["deduction", "forensics", "pattern-recognition"],
        "traits": ["analytical", "blunt"]
      },
      "score": 88.8,
      "breakdown": {
        "skills_score": 45.0,
        "experience_score": 22.5,
        "culture_score": 11.25,
        "availability_score": 10.0
      },
      "matched_skills": ["deduction", "forensics", "pattern-recognition"],
      "missing_skills": [],
      "matched_traits": ["analytical", "blunt~autonomous"],
      "reason": "Perfect skill match (3/3: deduction, forensics, pattern-recognition). 8 yrs exp meets min 3 yrs (+5 yrs seniority bonus). Culture synergy on 'analytical'. Available immediately. Quirk heads-up: \"Solves problems by eliminating the impossible; occasionally insufferable in standups.\"."
    }
  ]
}
```

### 2. Ranked Jobs for a Candidate (Reverse Direction)
`GET /candidates/{id}/matches`

```bash
curl -X GET "http://localhost:8000/candidates/2/matches" -H "Accept: application/json"
```

**Output**: Returns all 6 jobs ranked for Hermione Granger, with Developer Relations Lead ranking #1 (Score: 82.0).

### 3. List All Jobs
`GET /jobs`
```bash
curl -X GET "http://localhost:8000/jobs"
```

### 4. List All Candidates
`GET /candidates`
```bash
curl -X GET "http://localhost:8000/candidates"
```

### 5. Ingest Candidate Profile
`POST /candidates`
```bash
curl -X POST "http://localhost:8000/candidates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Benoit Blanc",
    "experience_years": 14,
    "availability": "Immediate",
    "quirk": "Speaks in elaborate donut metaphors.",
    "skills": ["deduction", "forensics", "observation"],
    "traits": ["analytical", "eccentric"]
  }'
```

### 6. Ingest Job Opening
`POST /jobs`
```bash
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Lead Mystery Investigator",
    "min_experience": 5,
    "tagline": "The donut hole inside the donut.",
    "required_skills": ["deduction", "observation"],
    "culture_keywords": ["analytical"]
  }'
```

---

## Part 2: The SQL Detective Challenge

All answers are provided in [`sql_detective.sql`](file:///c:/Users/rajat/OneDrive/Desktop/recruiterflow/sql_detective.sql). Run the automated verifier to execute and view the formatted output:

```bash
python run_sql_detective.py
```

### Summary of Detective Questions & Solutions

#### Question 1: Open Job Postings with Recruiter Owner
- **Query**: Inner joins `job_postings` with `recruiters` filtering `WHERE jp.status = 'open'`.
- **Result**: 4 postings returned (Jobs 1, 2, 4, 5 owned by Priya Shah, Daniel Ortiz, Wei Zhang).

#### Question 2: Final Stage Applicants per Job Posting
- **Query**: `LEFT JOIN` on `interviews` where `stage = 'Final'`, grouping by job posting with `COUNT(DISTINCT i.applicant_id)`.
- **Result**:
  - Jobs 1, 2, 4, 7: 2 applicants
  - Job 3: 1 applicant
  - Jobs 5, 6: 0 applicants

#### Question 3: Candidates Applying to Multiple Postings (Dirty Data Trap)
- **Detective Catch**:
  Applicant ID 1 (`ananya.rao@mail.com`) applied to Job 1, while Applicant ID 2 (`Ananya.Rao@mail.com`) applied to Job 4.
  Grouping strictly by `applicant_id` misses this duplicate.
  We normalize identity with `LOWER(TRIM(a.email))` and count `DISTINCT i.job_posting_id`.
- **Result**:
  1. **Ananya Rao** (`ananya.rao@mail.com`) — 2 distinct jobs (1, 4)
  2. **Ben Turner** (`ben.turner@mail.com`) — 2 distinct jobs (1, 3)
  3. **Elena Popescu** (`elena.popescu@mail.com`) — 2 distinct jobs (2, 7)

#### Question 4: Recruiter Final-Stage Conversion Rate (Min 3 Final Interviews)
- **Query**: Computes `SUM(passed) / COUNT(*)` for `stage = 'Final'`, grouped by recruiter with `HAVING COUNT(i.id) >= 3`.
- **Trap Avoidance**: Multiplies by `1.0` to avoid SQLite/SQL integer division truncation.
- **Result**:
  - **Priya Shah**: 3 passed / 4 total = **0.7500 (75.0%)**
  - **Daniel Ortiz**: 2 passed / 4 total = **0.5000 (50.0%)**
  - *(Fatima Al-Sayed, Wei Zhang, and Grace Okafor have fewer than 3 Final interviews and are correctly excluded).*

#### Question 5 (Bonus): Top Recruiter per Department via Window Function
- **Query**: Uses `DENSE_RANK() OVER (PARTITION BY jp.department ORDER BY COUNT(i.id) DESC)` inside a CTE, filtering `WHERE rank_in_dept = 1`.
- **Result**:
  - **Engineering**: Priya Shah (3 placements)
  - **Data**: Fatima Al-Sayed (1 placement)

---

## Automated Testing

The project includes unit and integration tests across the API, matching engine, and SQL detective queries.

Run tests:
```bash
python -m pytest -v
```

**Results (20 tests passed, 0 failures):**
- `tests/test_matcher.py`: Verifies skill overlap calculation, breadth bonus, experience penalties, availability weighting, and character tie-breakers.
- `tests/test_api.py`: Tests all REST endpoints using FastAPI TestClient, including ranking outputs, 404 handling, and end-to-end ingestion.
- `tests/test_sql_detective.py`: Verifies all 5 SQL detective queries against the hiring ops dataset.

---

## AI Tools Disclosure

As requested in the submission prompt, here is an honest disclosure of how AI tools were utilized:
- **Ideation & Scaffolding**: An AI pair programmer (Antigravity with Gemini 3.8 Flash) was used to bootstrap boilerplate structures, draft the Pydantic v2 model definitions, and assist in designing the semantic trait synonym dictionary.
- **SQL Analysis**: AI assisted in rapidly identifying edge cases in the messy hiring ops dataset (specifically the case-insensitive email collision in Question 3).
- **Test Generation**: Automated pytest assertions and mock payloads were generated with AI assistance to ensure 100% test coverage across both parts.
- **Algorithm Formulation**: The mathematical scoring weights (50/25/15/10), seniority curves, and tie-breaking strategy were engineered to reflect real-world technical staffing practices.

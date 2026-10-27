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


# -----------------------------------------------------------------------------
# Part 2 Live SQL Detective Endpoint
# -----------------------------------------------------------------------------

SQL_DETECTIVE_QUESTIONS = {
    1: {
        "title": "Question 1: Open Job Postings with Recruiter Owner",
        "description": "List all currently open job postings, along with the name of the recruiter who owns each one.",
        "sql": """SELECT
    jp.id AS job_posting_id,
    jp.title AS job_title,
    jp.department,
    r.name AS recruiter_name,
    jp.opened_date,
    jp.status
FROM job_postings jp
INNER JOIN recruiters r ON jp.recruiter_id = r.id
WHERE jp.status = 'open'
ORDER BY jp.id ASC;"""
    },
    2: {
        "title": "Question 2: Applicants Reaching Final Stage per Job",
        "description": "For each job posting, how many applicants reached the Final interview stage?",
        "sql": """SELECT
    jp.id AS job_posting_id,
    jp.title AS job_title,
    jp.department,
    COUNT(DISTINCT CASE WHEN i.stage = 'Final' THEN i.applicant_id END) AS final_stage_applicants_count
FROM job_postings jp
LEFT JOIN interviews i ON jp.id = i.job_posting_id AND i.stage = 'Final'
GROUP BY jp.id, jp.title, jp.department
ORDER BY jp.id ASC;"""
    },
    3: {
        "title": "Question 3: Multi-Job Applicants (Dirty Data Trap)",
        "description": "Find every person who effectively applied to more than one job posting. Normalizes email casing (e.g. ananya.rao@mail.com vs Ananya.Rao@mail.com).",
        "sql": """SELECT
    MIN(a.full_name) AS full_name,
    LOWER(TRIM(a.email)) AS normalized_email,
    COUNT(DISTINCT i.job_posting_id) AS distinct_jobs_applied
FROM applicants a
INNER JOIN interviews i ON a.id = i.applicant_id
GROUP BY LOWER(TRIM(a.email))
HAVING COUNT(DISTINCT i.job_posting_id) > 1
ORDER BY distinct_jobs_applied DESC, full_name ASC;"""
    },
    4: {
        "title": "Question 4: Recruiter Conversion Rate (>= 3 Final Interviews)",
        "description": "For each recruiter, compute their Final-stage conversion rate (passed ÷ total Final-stage interviews), but only include recruiters with at least 3 Final-stage interviews.",
        "sql": """SELECT
    r.id AS recruiter_id,
    r.name AS recruiter_name,
    r.region,
    COUNT(i.id) AS total_final_interviews,
    SUM(CASE WHEN i.outcome = 'passed' THEN 1 ELSE 0 END) AS passed_final_interviews,
    ROUND(
        1.0 * SUM(CASE WHEN i.outcome = 'passed' THEN 1 ELSE 0 END) / COUNT(i.id),
        4
    ) AS final_stage_conversion_rate
FROM recruiters r
INNER JOIN job_postings jp ON r.id = jp.recruiter_id
INNER JOIN interviews i ON jp.id = i.job_posting_id
WHERE i.stage = 'Final'
GROUP BY r.id, r.name, r.region
HAVING COUNT(i.id) >= 3
ORDER BY final_stage_conversion_rate DESC, total_final_interviews DESC;"""
    },
    5: {
        "title": "Question 5 (Bonus): Top Recruiter per Department via Window Function",
        "description": "Using a window function (DENSE_RANK), find the recruiter with the most successful placements (passed at Final stage) per department.",
        "sql": """WITH department_recruiter_placements AS (
    SELECT
        jp.department,
        r.id AS recruiter_id,
        r.name AS recruiter_name,
        COUNT(i.id) AS successful_placements,
        DENSE_RANK() OVER (
            PARTITION BY jp.department
            ORDER BY COUNT(i.id) DESC
        ) AS rank_in_dept
    FROM job_postings jp
    INNER JOIN recruiters r ON jp.recruiter_id = r.id
    INNER JOIN interviews i ON jp.id = i.job_posting_id
    WHERE i.stage = 'Final' AND i.outcome = 'passed'
    GROUP BY jp.department, r.id, r.name
)
SELECT
    department,
    recruiter_id,
    recruiter_name,
    successful_placements
FROM department_recruiter_placements
WHERE rank_in_dept = 1
ORDER BY department ASC;"""
    }
}


@router.get("/api/sql-detective/questions", summary="Get all SQL Detective questions")
def get_sql_detective_questions():
    """Returns the list of SQL Detective challenge questions."""
    return [
        {
            "id": q_id,
            "title": data["title"],
            "description": data["description"],
            "sql": data["sql"]
        }
        for q_id, data in SQL_DETECTIVE_QUESTIONS.items()
    ]


@router.get("/api/sql-detective/run/{question_id}", summary="Run SQL Detective query")
def run_sql_detective_query(question_id: int):
    """Executes a specific SQL Detective question in-memory and returns structured rows."""
    from run_sql_detective import PART2_SCHEMA, PART2_SEED
    if question_id not in SQL_DETECTIVE_QUESTIONS:
        return {"error": f"Question {question_id} not found. Valid IDs: 1 to 5."}

    q_data = SQL_DETECTIVE_QUESTIONS[question_id]
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.executescript(PART2_SCHEMA)
    cursor.executescript(PART2_SEED)
    conn.commit()

    cursor.execute(q_data["sql"])
    rows = [dict(r) for r in cursor.fetchall()]
    columns = [d[0] for d in cursor.description] if cursor.description else []
    conn.close()

    return {
        "question_id": question_id,
        "title": q_data["title"],
        "description": q_data["description"],
        "sql": q_data["sql"],
        "columns": columns,
        "rows": rows,
        "row_count": len(rows)
    }


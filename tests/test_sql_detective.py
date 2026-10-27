import sqlite3
import pytest
from run_sql_detective import PART2_SCHEMA, PART2_SEED


@pytest.fixture
def detective_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.executescript(PART2_SCHEMA)
    cursor.executescript(PART2_SEED)
    conn.commit()
    yield conn
    conn.close()


def test_question_1_open_job_postings(detective_db):
    query = """
        SELECT
            jp.id AS job_posting_id,
            jp.title AS job_title,
            jp.department,
            r.name AS recruiter_name,
            jp.opened_date,
            jp.status
        FROM job_postings jp
        INNER JOIN recruiters r ON jp.recruiter_id = r.id
        WHERE jp.status = 'open'
        ORDER BY jp.id ASC;
    """
    rows = detective_db.execute(query).fetchall()
    assert len(rows) == 4
    open_ids = [r["job_posting_id"] for r in rows]
    assert open_ids == [1, 2, 4, 5]
    # Check recruiter ownership
    recruiter_map = {r["job_posting_id"]: r["recruiter_name"] for r in rows}
    assert recruiter_map[1] == "Priya Shah"
    assert recruiter_map[2] == "Daniel Ortiz"
    assert recruiter_map[4] == "Priya Shah"
    assert recruiter_map[5] == "Wei Zhang"


def test_question_2_final_stage_applicants_per_job(detective_db):
    query = """
        SELECT
            jp.id AS job_posting_id,
            jp.title AS job_title,
            jp.department,
            COUNT(DISTINCT CASE WHEN i.stage = 'Final' THEN i.applicant_id END) AS final_stage_applicants_count
        FROM job_postings jp
        LEFT JOIN interviews i ON jp.id = i.job_posting_id AND i.stage = 'Final'
        GROUP BY jp.id, jp.title, jp.department
        ORDER BY jp.id ASC;
    """
    rows = detective_db.execute(query).fetchall()
    assert len(rows) == 7
    counts = {r["job_posting_id"]: r["final_stage_applicants_count"] for r in rows}
    assert counts[1] == 2
    assert counts[2] == 2
    assert counts[3] == 1
    assert counts[4] == 2
    assert counts[5] == 0
    assert counts[6] == 0
    assert counts[7] == 2


def test_question_3_multiple_job_applicants(detective_db):
    query = """
        SELECT
            MIN(a.full_name) AS full_name,
            LOWER(TRIM(a.email)) AS normalized_email,
            COUNT(DISTINCT i.job_posting_id) AS distinct_jobs_applied
        FROM applicants a
        INNER JOIN interviews i ON a.id = i.applicant_id
        GROUP BY LOWER(TRIM(a.email))
        HAVING COUNT(DISTINCT i.job_posting_id) > 1
        ORDER BY distinct_jobs_applied DESC, full_name ASC;
    """
    rows = detective_db.execute(query).fetchall()
    assert len(rows) == 3
    emails = {r["normalized_email"] for r in rows}
    names = {r["full_name"] for r in rows}
    # Verifies that Ananya Rao was caught despite email casing difference
    assert "ananya.rao@mail.com" in emails
    assert "ben.turner@mail.com" in emails
    assert "elena.popescu@mail.com" in emails
    assert "Ananya Rao" in names
    assert "Ben Turner" in names
    assert "Elena Popescu" in names


def test_question_4_recruiter_conversion_rate(detective_db):
    query = """
        SELECT
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
        ORDER BY final_stage_conversion_rate DESC, total_final_interviews DESC;
    """
    rows = detective_db.execute(query).fetchall()
    assert len(rows) == 2
    rates = {r["recruiter_name"]: r["final_stage_conversion_rate"] for r in rows}
    # Priya Shah: 3 passed out of 4 = 0.75
    assert rates["Priya Shah"] == 0.75
    # Daniel Ortiz: 2 passed out of 4 = 0.50
    assert rates["Daniel Ortiz"] == 0.50


def test_question_5_top_recruiter_per_department(detective_db):
    query = """
        WITH department_recruiter_placements AS (
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
        ORDER BY department ASC;
    """
    rows = detective_db.execute(query).fetchall()
    assert len(rows) == 2
    dept_map = {r["department"]: r["recruiter_name"] for r in rows}
    assert dept_map["Engineering"] == "Priya Shah"
    assert dept_map["Data"] == "Fatima Al-Sayed"

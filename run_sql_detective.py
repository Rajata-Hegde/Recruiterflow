"""
Runner and Verification Script for Part 2: The SQL Detective Challenge.
Executes the schema, seed data, and each SQL Detective query in SQLite,
displaying nicely formatted results.
"""

import sqlite3
import re

PART2_SCHEMA = """
CREATE TABLE recruiters (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    region VARCHAR(50)
);

CREATE TABLE job_postings (
    id INT PRIMARY KEY,
    title VARCHAR(100),
    recruiter_id INT,
    department VARCHAR(50),
    opened_date DATE,
    status VARCHAR(20) -- 'open', 'closed', 'on_hold'
);

CREATE TABLE applicants (
    id INT PRIMARY KEY,
    full_name VARCHAR(100),
    email VARCHAR(100),
    source VARCHAR(50), -- nullable
    applied_date DATE
);

CREATE TABLE interviews (
    id INT PRIMARY KEY,
    applicant_id INT,
    job_posting_id INT,
    stage VARCHAR(20), -- 'Screen', 'Technical', 'Final'
    scheduled_date DATE,
    outcome VARCHAR(20) -- 'passed', 'failed', 'no_show', NULL (pending)
);
"""

PART2_SEED = """
INSERT INTO recruiters VALUES
(1, 'Priya Shah', 'APAC'),
(2, 'Daniel Ortiz', 'NA'),
(3, 'Fatima Al-Sayed', 'EMEA'),
(4, 'Wei Zhang', 'APAC'),
(5, 'Grace Okafor', 'EMEA');

INSERT INTO job_postings VALUES
(1, 'Backend Engineer I', 1, 'Engineering', '2026-01-05', 'open'),
(2, 'Backend Engineer I', 2, 'Engineering', '2026-01-10', 'open'),
(3, 'Data Analyst', 3, 'Data', '2026-01-08', 'closed'),
(4, 'Backend Engineer II', 1, 'Engineering', '2026-02-01', 'open'),
(5, 'DevOps Engineer', 4, 'Infrastructure', '2026-01-20', 'open'),
(6, 'Data Analyst', 5, 'Data', '2026-02-05', 'on_hold'),
(7, 'Backend Engineer I', 2, 'Engineering', '2026-02-15', 'closed');

INSERT INTO applicants VALUES
(1, 'Ananya Rao', 'ananya.rao@mail.com', 'LinkedIn', '2026-01-06'),
(2, 'Ananya Rao', 'Ananya.Rao@mail.com', 'Referral', '2026-02-04'),
(3, 'Ben Turner', 'ben.turner@mail.com', 'Job Board', '2026-01-07'),
(4, 'Chloe Martin', 'chloe.martin@mail.com', NULL, '2026-01-09'),
(5, 'Devansh Patel', 'devansh.patel@mail.com', 'LinkedIn', '2026-01-11'),
(6, 'Elena Popescu', 'elena.popescu@mail.com', 'Referral', '2026-01-12'),
(7, 'Farid Haidari', 'farid.haidari@mail.com', 'Job Board', '2026-01-13'),
(8, 'Grace Lin', 'grace.lin@mail.com', 'LinkedIn', '2026-01-15'),
(9, 'Hassan Malik', 'hassan.malik@mail.com', NULL, '2026-01-16'),
(10, 'Isla Fraser', 'isla.fraser@mail.com', 'Referral', '2026-01-18'),
(11, 'Jonas Weber', 'jonas.weber@mail.com', 'Job Board', '2026-02-10');

INSERT INTO interviews VALUES
(1, 1, 1, 'Screen', '2026-01-10', 'passed'),
(2, 1, 1, 'Technical', '2026-01-15', 'passed'),
(3, 1, 1, 'Final', '2026-01-22', 'passed'),
(4, 2, 4, 'Screen', '2026-02-05', 'passed'),
(5, 3, 1, 'Screen', '2026-01-11', 'passed'),
(6, 3, 1, 'Technical', '2026-01-16', 'failed'),
(7, 3, 3, 'Final', '2026-01-28', 'passed'),
(8, 4, 1, 'Screen', '2026-01-12', 'passed'),
(9, 4, 1, 'Final', '2026-01-24', 'failed'),
(10, 5, 2, 'Screen', '2026-01-14', 'passed'),
(11, 5, 2, 'Technical', '2026-01-19', 'passed'),
(12, 5, 2, 'Final', '2026-01-25', 'passed'),
(13, 6, 2, 'Screen', '2026-01-15', 'passed'),
(14, 6, 2, 'Final', '2026-01-26', 'failed'),
(15, 7, 2, 'Screen', '2026-01-16', 'no_show'),
(16, 8, 4, 'Screen', '2026-02-03', 'passed'),
(17, 8, 4, 'Technical', '2026-02-08', 'passed'),
(18, 8, 4, 'Final', '2026-02-12', 'passed'),
(19, 9, 4, 'Screen', '2026-02-04', 'passed'),
(20, 9, 4, 'Final', '2026-02-14', 'passed'),
(21, 10, 5, 'Screen', '2026-01-22', 'passed'),
(22, 10, 5, 'Technical', '2026-01-28', NULL),
(23, 11, 7, 'Final', '2026-02-20', 'passed'),
(24, 6, 7, 'Final', '2026-02-21', 'failed');
"""


def format_table(cursor, rows):
    """Simple text table formatter."""
    if not rows:
        return "(0 rows returned)"
    headers = [desc[0] for desc in cursor.description]
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(val)))

    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_line = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    row_lines = [
        " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
        for row in rows
    ]
    return f"{header_line}\n{sep_line}\n" + "\n".join(row_lines)


def main():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    print("[*] Setting up in-memory SQLite database for Part 2...")
    cursor.executescript(PART2_SCHEMA)
    cursor.executescript(PART2_SEED)
    conn.commit()

    # Dedicated queries matching sql_detective.sql
    queries = [
        ("Question 1: Open job postings with recruiter owner", """
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
        """),
        ("Question 2: Applicants reaching Final stage per job posting", """
            SELECT
                jp.id AS job_posting_id,
                jp.title AS job_title,
                jp.department,
                COUNT(DISTINCT CASE WHEN i.stage = 'Final' THEN i.applicant_id END) AS final_stage_applicants_count
            FROM job_postings jp
            LEFT JOIN interviews i ON jp.id = i.job_posting_id AND i.stage = 'Final'
            GROUP BY jp.id, jp.title, jp.department
            ORDER BY jp.id ASC;
        """),
        ("Question 3: Persons who effectively applied to more than one job posting", """
            SELECT
                MIN(a.full_name) AS full_name,
                LOWER(TRIM(a.email)) AS normalized_email,
                COUNT(DISTINCT i.job_posting_id) AS distinct_jobs_applied
            FROM applicants a
            INNER JOIN interviews i ON a.id = i.applicant_id
            GROUP BY LOWER(TRIM(a.email))
            HAVING COUNT(DISTINCT i.job_posting_id) > 1
            ORDER BY distinct_jobs_applied DESC, full_name ASC;
        """),
        ("Question 4: Recruiter Final-stage conversion rate (minimum 3 Final interviews)", """
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
        """),
        ("Question 5 (Bonus): Top recruiter with most successful placements per department", """
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
        """)
    ]

    for title, query in queries:
        print("=" * 80)
        print(f"{title}")
        print("=" * 80)
        cursor.execute(query.strip())
        rows = cursor.fetchall()
        print(format_table(cursor, rows))
        print(f"\n({len(rows)} row(s) returned)\n")

    conn.close()


if __name__ == "__main__":
    main()

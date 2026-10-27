-- ============================================================================
-- RecruiterFlow - Part 2: The SQL Detective Challenge
-- Candidate: RecruiterFlow Assignment Submission
-- File: sql_detective.sql
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Question 1: List all currently open job postings, along with the name of
-- the recruiter who owns each one.
-- ----------------------------------------------------------------------------
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


-- ----------------------------------------------------------------------------
-- Question 2: For each job posting, how many applicants reached the Final
-- interview stage?
-- ----------------------------------------------------------------------------
SELECT
    jp.id AS job_posting_id,
    jp.title AS job_title,
    jp.department,
    COUNT(DISTINCT CASE WHEN i.stage = 'Final' THEN i.applicant_id END) AS final_stage_applicants_count
FROM job_postings jp
LEFT JOIN interviews i ON jp.id = i.job_posting_id AND i.stage = 'Final'
GROUP BY jp.id, jp.title, jp.department
ORDER BY jp.id ASC;


-- ----------------------------------------------------------------------------
-- Question 3: Find every person who effectively applied to more than one job
-- posting. Careful — the data isn't as clean as it looks.
--
-- Detective Note:
-- The data contains duplicate applicant records for the same physical person
-- created with varying email casing (e.g. 'ananya.rao@mail.com' with id=1
-- applied to job 1, and 'Ananya.Rao@mail.com' with id=2 applied to job 4).
-- Grouping strictly by applicant_id fails to capture this duplicate.
-- We normalize the person's identity via LOWER(TRIM(a.email)) and aggregate
-- DISTINCT job_posting_id to identify people who applied to multiple jobs.
-- ----------------------------------------------------------------------------
SELECT
    MIN(a.full_name) AS full_name,
    LOWER(TRIM(a.email)) AS normalized_email,
    COUNT(DISTINCT i.job_posting_id) AS distinct_jobs_applied
FROM applicants a
INNER JOIN interviews i ON a.id = i.applicant_id
GROUP BY LOWER(TRIM(a.email))
HAVING COUNT(DISTINCT i.job_posting_id) > 1
ORDER BY distinct_jobs_applied DESC, full_name ASC;


-- ----------------------------------------------------------------------------
-- Question 4: For each recruiter, compute their Final-stage conversion rate
-- (passed ÷ total Final-stage interviews), but only include recruiters with
-- at least 3 Final-stage interviews.
-- ----------------------------------------------------------------------------
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


-- ----------------------------------------------------------------------------
-- Question 5 (Bonus): Using a window function, find the recruiter with the
-- most successful placements (passed at Final stage) per department.
-- ----------------------------------------------------------------------------
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

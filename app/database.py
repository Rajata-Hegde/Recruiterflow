"""
Database module for Recruiter Bot.
Interacts with SQLite purely via raw, hand-written SQL.
NO ORMs or query builder abstractions used.
"""

import sqlite3
from typing import Generator, List, Dict, Any, Optional
from app.config import DB_PATH, DDL_FILE_PATH, SEED_FILE_PATH


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create a new SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency for obtaining a database connection."""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize database tables using the hand-written ddl.sql script."""
    with open(DDL_FILE_PATH, "r", encoding="utf-8") as f:
        ddl_script = f.read()

    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executescript(ddl_script)
        conn.commit()
    finally:
        conn.close()


def seed_db(db_path: str = DB_PATH) -> None:
    """Seed the database with initial candidates and jobs using seed.sql."""
    with open(SEED_FILE_PATH, "r", encoding="utf-8") as f:
        seed_script = f.read()

    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executescript(seed_script)
        conn.commit()
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# Raw SQL Data Access Helpers - Candidates
# -----------------------------------------------------------------------------

def fetch_all_candidates(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Retrieve all candidates with their associated skills and traits via raw SQL."""
    cursor = conn.cursor()
    
    # 1. Fetch all candidate master records
    candidates_query = """
        SELECT id, name, experience_years, availability, quirk, created_at
        FROM candidates
        ORDER BY id ASC;
    """
    candidates = [dict(row) for row in cursor.execute(candidates_query).fetchall()]
    
    if not candidates:
        return []

    # 2. Fetch all skills
    skills_query = """
        SELECT candidate_id, skill
        FROM candidate_skills
        ORDER BY candidate_id ASC, skill ASC;
    """
    skills_by_id: Dict[int, List[str]] = {}
    for row in cursor.execute(skills_query).fetchall():
        cid = row["candidate_id"]
        skills_by_id.setdefault(cid, []).append(row["skill"])

    # 3. Fetch all traits
    traits_query = """
        SELECT candidate_id, trait
        FROM candidate_traits
        ORDER BY candidate_id ASC, trait ASC;
    """
    traits_by_id: Dict[int, List[str]] = {}
    for row in cursor.execute(traits_query).fetchall():
        cid = row["candidate_id"]
        traits_by_id.setdefault(cid, []).append(row["trait"])

    for c in candidates:
        cid = c["id"]
        c["skills"] = skills_by_id.get(cid, [])
        c["traits"] = traits_by_id.get(cid, [])

    return candidates


def fetch_candidate_by_id(conn: sqlite3.Connection, candidate_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single candidate by ID with associated skills and traits."""
    cursor = conn.cursor()
    candidate_query = """
        SELECT id, name, experience_years, availability, quirk, created_at
        FROM candidates
        WHERE id = ?;
    """
    candidate_row = cursor.execute(candidate_query, (candidate_id,)).fetchone()
    if not candidate_row:
        return None

    candidate = dict(candidate_row)

    skills_query = """
        SELECT skill
        FROM candidate_skills
        WHERE candidate_id = ?
        ORDER BY skill ASC;
    """
    candidate["skills"] = [row["skill"] for row in cursor.execute(skills_query, (candidate_id,)).fetchall()]

    traits_query = """
        SELECT trait
        FROM candidate_traits
        WHERE candidate_id = ?
        ORDER BY trait ASC;
    """
    candidate["traits"] = [row["trait"] for row in cursor.execute(traits_query, (candidate_id,)).fetchall()]

    return candidate


def insert_candidate(
    conn: sqlite3.Connection,
    name: str,
    experience_years: int,
    availability: str,
    quirk: str,
    skills: List[str],
    traits: List[str]
) -> int:
    """Insert a new candidate along with their skills and traits using raw SQL."""
    cursor = conn.cursor()
    
    insert_candidate_sql = """
        INSERT INTO candidates (name, experience_years, availability, quirk)
        VALUES (?, ?, ?, ?);
    """
    cursor.execute(insert_candidate_sql, (name, experience_years, availability, quirk))
    candidate_id = cursor.lastrowid

    if skills:
        insert_skill_sql = """
            INSERT OR IGNORE INTO candidate_skills (candidate_id, skill)
            VALUES (?, ?);
        """
        for skill in set(skills):
            normalized_skill = skill.strip().lower()
            if normalized_skill:
                cursor.execute(insert_skill_sql, (candidate_id, normalized_skill))

    if traits:
        insert_trait_sql = """
            INSERT OR IGNORE INTO candidate_traits (candidate_id, trait)
            VALUES (?, ?);
        """
        for trait in set(traits):
            normalized_trait = trait.strip().lower()
            if normalized_trait:
                cursor.execute(insert_trait_sql, (candidate_id, normalized_trait))

    conn.commit()
    return candidate_id


# -----------------------------------------------------------------------------
# Raw SQL Data Access Helpers - Jobs
# -----------------------------------------------------------------------------

def fetch_all_jobs(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Retrieve all jobs with required skills and culture keywords via raw SQL."""
    cursor = conn.cursor()
    
    jobs_query = """
        SELECT id, title, min_experience, tagline, created_at
        FROM jobs
        ORDER BY id ASC;
    """
    jobs = [dict(row) for row in cursor.execute(jobs_query).fetchall()]
    if not jobs:
        return []

    skills_query = """
        SELECT job_id, skill
        FROM job_skills
        ORDER BY job_id ASC, skill ASC;
    """
    skills_by_id: Dict[int, List[str]] = {}
    for row in cursor.execute(skills_query).fetchall():
        jid = row["job_id"]
        skills_by_id.setdefault(jid, []).append(row["skill"])

    culture_query = """
        SELECT job_id, keyword
        FROM job_culture_keywords
        ORDER BY job_id ASC, keyword ASC;
    """
    culture_by_id: Dict[int, List[str]] = {}
    for row in cursor.execute(culture_query).fetchall():
        jid = row["job_id"]
        culture_by_id.setdefault(jid, []).append(row["keyword"])

    for j in jobs:
        jid = j["id"]
        j["required_skills"] = skills_by_id.get(jid, [])
        j["culture_keywords"] = culture_by_id.get(jid, [])

    return jobs


def fetch_job_by_id(conn: sqlite3.Connection, job_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single job by ID with required skills and culture keywords."""
    cursor = conn.cursor()
    job_query = """
        SELECT id, title, min_experience, tagline, created_at
        FROM jobs
        WHERE id = ?;
    """
    job_row = cursor.execute(job_query, (job_id,)).fetchone()
    if not job_row:
        return None

    job = dict(job_row)

    skills_query = """
        SELECT skill
        FROM job_skills
        WHERE job_id = ?
        ORDER BY skill ASC;
    """
    job["required_skills"] = [row["skill"] for row in cursor.execute(skills_query, (job_id,)).fetchall()]

    culture_query = """
        SELECT keyword
        FROM job_culture_keywords
        WHERE job_id = ?
        ORDER BY keyword ASC;
    """
    job["culture_keywords"] = [row["keyword"] for row in cursor.execute(culture_query, (job_id,)).fetchall()]

    return job


def insert_job(
    conn: sqlite3.Connection,
    title: str,
    min_experience: int,
    tagline: str,
    required_skills: List[str],
    culture_keywords: List[str]
) -> int:
    """Insert a new job opening along with required skills and culture keywords."""
    cursor = conn.cursor()
    
    insert_job_sql = """
        INSERT INTO jobs (title, min_experience, tagline)
        VALUES (?, ?, ?);
    """
    cursor.execute(insert_job_sql, (title, min_experience, tagline))
    job_id = cursor.lastrowid

    if required_skills:
        insert_skill_sql = """
            INSERT OR IGNORE INTO job_skills (job_id, skill)
            VALUES (?, ?);
        """
        for skill in set(required_skills):
            normalized_skill = skill.strip().lower()
            if normalized_skill:
                cursor.execute(insert_skill_sql, (job_id, normalized_skill))

    if culture_keywords:
        insert_culture_sql = """
            INSERT OR IGNORE INTO job_culture_keywords (job_id, keyword)
            VALUES (?, ?);
        """
        for keyword in set(culture_keywords):
            normalized_keyword = keyword.strip().lower()
            if normalized_keyword:
                cursor.execute(insert_culture_sql, (job_id, normalized_keyword))

    conn.commit()
    return job_id


def log_match_history(
    conn: sqlite3.Connection,
    job_id: int,
    candidate_id: int,
    score: float,
    reason: str
) -> None:
    """Audit log of ranked matches generated by the system."""
    cursor = conn.cursor()
    insert_sql = """
        INSERT INTO match_history (job_id, candidate_id, score, reason)
        VALUES (?, ?, ?, ?);
    """
    cursor.execute(insert_sql, (job_id, candidate_id, score, reason))
    conn.commit()

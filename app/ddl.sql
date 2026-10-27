-- ============================================================================
-- RecruiterFlow Recruiter Bot - Core Database Schema (DDL)
-- Hand-written raw SQL. No ORMs or query builders.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- 1. Candidates Table
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
    availability TEXT NOT NULL CHECK (availability IN ('Immediate', '2 weeks', 'Not looking')),
    quirk TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Candidate Skills Table (Normalized 1:N)
CREATE TABLE IF NOT EXISTS candidate_skills (
    candidate_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    PRIMARY KEY (candidate_id, skill),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

-- 3. Candidate Traits Table (Normalized 1:N)
CREATE TABLE IF NOT EXISTS candidate_traits (
    candidate_id INTEGER NOT NULL,
    trait TEXT NOT NULL,
    PRIMARY KEY (candidate_id, trait),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

-- 4. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    min_experience INTEGER NOT NULL CHECK (min_experience >= 0),
    tagline TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Job Required Skills Table (Normalized 1:N)
CREATE TABLE IF NOT EXISTS job_skills (
    job_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    PRIMARY KEY (job_id, skill),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- 6. Job Culture Keywords Table (Normalized 1:N)
CREATE TABLE IF NOT EXISTS job_culture_keywords (
    job_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    PRIMARY KEY (job_id, keyword),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- 7. Match History / Audit Log (Optional analytical store)
CREATE TABLE IF NOT EXISTS match_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    score REAL NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

-- Indexes for lightning-fast join and matching performance
CREATE INDEX IF NOT EXISTS idx_candidate_skills_skill ON candidate_skills(skill);
CREATE INDEX IF NOT EXISTS idx_candidate_traits_trait ON candidate_traits(trait);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill);
CREATE INDEX IF NOT EXISTS idx_job_culture_keywords_keyword ON job_culture_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_candidates_experience ON candidates(experience_years);
CREATE INDEX IF NOT EXISTS idx_candidates_availability ON candidates(availability);
CREATE INDEX IF NOT EXISTS idx_jobs_min_experience ON jobs(min_experience);

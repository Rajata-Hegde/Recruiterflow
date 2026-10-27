"""
CLI Seeder Script for RecruiterFlow Recruiter Bot.
Usage:
    python seed.py
"""

import sys
from app.database import init_db, seed_db, get_db_connection, fetch_all_candidates, fetch_all_jobs


def main():
    print("[*] Initializing RecruiterFlow database schema from app/ddl.sql...")
    init_db()
    print("[*] Seeding candidates and jobs from app/seed.sql...")
    seed_db()

    conn = get_db_connection()
    try:
        candidates = fetch_all_candidates(conn)
        jobs = fetch_all_jobs(conn)
        print(f"[+] Successfully loaded {len(candidates)} candidates and {len(jobs)} jobs into SQLite database!")
        print("-" * 60)
        print("Sample Candidates:")
        for c in candidates[:3]:
            print(f"  - {c['name']} ({c['experience_years']} yrs, {c['availability']}) | Skills: {', '.join(c['skills'])}")
        print("-" * 60)
        print("Sample Jobs:")
        for j in jobs[:3]:
            print(f"  - {j['title']} (min {j['min_experience']} yrs) | Skills: {', '.join(j['required_skills'])}")
        print("-" * 60)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

"""
Demo Script for RecruiterFlow Recruiter Bot.
Demonstrates ranking results for both jobs and candidates.
Usage:
    python demo.py
"""

from app.database import init_db, seed_db, get_db_connection, fetch_all_jobs, fetch_all_candidates
from app.matcher import rank_candidates_for_job, rank_jobs_for_candidate


def main():
    init_db()
    seed_db()
    conn = get_db_connection()
    try:
        jobs = fetch_all_jobs(conn)
        candidates = fetch_all_candidates(conn)

        print("\n" + "=" * 90)
        print(" RECRUITERFLOW RECRUITER BOT - TOP MATCHES FOR EACH JOB")
        print("=" * 90)

        for job in jobs:
            print(f"\n[JOB #{job['id']}] {job['title']} (Min Exp: {job['min_experience']} yrs)")
            print(f"Tagline: \"{job['tagline']}\"")
            print(f"Required Skills: {', '.join(job['required_skills'])}")
            print(f"Culture Keywords: {', '.join(job['culture_keywords'])}")
            print("-" * 90)

            ranked = rank_candidates_for_job(candidates, job)
            for m in ranked[:3]:
                cand = m["candidate"]
                b = m["breakdown"]
                print(f"  #{m['rank']} {cand['name']:<14} | Total: {m['score']:>4.1f}/100 | (Skills: {b['skills_score']:>4.1f}, Exp: {b['experience_score']:>4.1f}, Culture: {b['culture_score']:>4.1f}, Avail: {b['availability_score']:>4.1f})")
                print(f"     Reason: {m['reason']}")

        print("\n" + "=" * 90)
        print(" REVERSE MATCHING DEMO - TOP JOBS FOR CANDIDATES")
        print("=" * 90)

        sample_candidates = [candidates[0], candidates[1], candidates[5]]  # Sherlock, Hermione, Rick
        for cand in sample_candidates:
            print(f"\n[CANDIDATE #{cand['id']}] {cand['name']} ({cand['experience_years']} yrs, {cand['availability']})")
            print(f"Skills: {', '.join(cand['skills'])}")
            print(f"Traits: {', '.join(cand['traits'])}")
            print(f"Quirk: \"{cand['quirk']}\"")
            print("-" * 90)

            ranked_jobs = rank_jobs_for_candidate(cand, jobs)
            for m in ranked_jobs[:2]:
                j = m["job"]
                b = m["breakdown"]
                print(f"  #{m['rank']} {j['title']:<32} | Score: {m['score']:>4.1f}/100 | (Skills: {b['skills_score']:>4.1f}, Exp: {b['experience_score']:>4.1f}, Culture: {b['culture_score']:>4.1f}, Avail: {b['availability_score']:>4.1f})")
                print(f"     Reason: {m['reason']}")

        print("\n" + "=" * 90)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

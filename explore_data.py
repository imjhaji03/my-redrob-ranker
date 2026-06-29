
import json
import os
from collections import Counter
from datetime import datetime, date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
SAMPLE_FILE = os.path.join(DATA_DIR, "sample_candidates.json")


def load_candidates(filepath):
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def print_section(title):
    
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def explore_basic_info(candidates):
    
    print_section("CANDIDATE OVERVIEW (ID, Experience, Title, Company, Top 5 Skills)")

    for i, cand in enumerate(candidates):
        cid = cand["candidate_id"]
        profile = cand["profile"]
        yoe = profile["years_of_experience"]
        title = profile["current_title"]
        company = profile["current_company"]

        # Get top 5 skills sorted by proficiency level and endorsements
        proficiency_order = {"expert": 4, "advanced": 3, "intermediate": 2, "beginner": 1}
        skills = sorted(
            cand.get("skills", []),
            key=lambda s: (proficiency_order.get(s.get("proficiency", "beginner"), 0),
                           s.get("endorsements", 0)),
            reverse=True
        )[:5]
        skill_str = ", ".join(
            f"{s['name']}({s['proficiency'][0].upper()},{s.get('duration_months',0)}mo)"
            for s in skills
        )

        print(f"\n  [{i+1:3d}] {cid} | {yoe:.1f} yrs | {title:<35s} | {company}")
        print(f"        Skills: {skill_str}")


def explore_redrob_signals(candidates):
    
    print_section("REDROB SIGNALS — Available Fields & Statistics")

    # Collect all signal keys
    all_signals = set()
    for cand in candidates:
        signals = cand.get("redrob_signals", {})
        all_signals.update(signals.keys())

    print(f"\n  Total signal fields found: {len(all_signals)}")
    print(f"\n  Signal fields:")
    for sig in sorted(all_signals):
        print(f"    - {sig}")

    # Compute statistics for numeric signals
    numeric_signals = {}
    for cand in candidates:
        signals = cand.get("redrob_signals", {})
        for key, val in signals.items():
            if isinstance(val, (int, float)):
                if key not in numeric_signals:
                    numeric_signals[key] = []
                numeric_signals[key].append(val)

    print(f"\n  Numeric Signal Statistics:")
    print(f"  {'Signal':<40s} {'Min':>8s} {'Max':>8s} {'Mean':>8s} {'Median':>8s}")
    print(f"  {'-'*40} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    for key in sorted(numeric_signals.keys()):
        vals = numeric_signals[key]
        vals_sorted = sorted(vals)
        n = len(vals)
        minimum = min(vals)
        maximum = max(vals)
        mean = sum(vals) / n
        median = vals_sorted[n // 2] if n % 2 == 1 else (vals_sorted[n // 2 - 1] + vals_sorted[n // 2]) / 2
        print(f"  {key:<40s} {minimum:>8.2f} {maximum:>8.2f} {mean:>8.2f} {median:>8.2f}")

    # Boolean signals
    bool_signals = {}
    for cand in candidates:
        signals = cand.get("redrob_signals", {})
        for key, val in signals.items():
            if isinstance(val, bool):
                if key not in bool_signals:
                    bool_signals[key] = Counter()
                bool_signals[key][val] += 1

    print(f"\n  Boolean Signal Distributions:")
    for key in sorted(bool_signals.keys()):
        counts = bool_signals[key]
        true_pct = counts.get(True, 0) / sum(counts.values()) * 100
        print(f"    {key:<35s} True: {counts.get(True,0):>3d} ({true_pct:.0f}%)  False: {counts.get(False,0):>3d}")


def explore_title_distribution(candidates):
   
    print_section("TITLE DISTRIBUTION")

    titles = Counter(c["profile"]["current_title"] for c in candidates)
    print(f"\n  Unique titles: {len(titles)}")
    for title, count in titles.most_common():
        print(f"    {title:<45s} {count:>3d}")


def explore_company_distribution(candidates):
    
    print_section("COMPANY DISTRIBUTION")

    companies = Counter(c["profile"]["current_company"] for c in candidates)
    print(f"\n  Unique companies: {len(companies)}")
    for company, count in companies.most_common(30):
        print(f"    {company:<45s} {count:>3d}")


def explore_industry_distribution(candidates):
    
    print_section("INDUSTRY DISTRIBUTION")

    industries = Counter(c["profile"]["current_industry"] for c in candidates)
    for ind, count in industries.most_common():
        print(f"    {ind:<45s} {count:>3d}")


def explore_skills_distribution(candidates):
    
    print_section("SKILL FREQUENCY (Top 40 most common skills)")

    skill_counter = Counter()
    for cand in candidates:
        for skill in cand.get("skills", []):
            skill_counter[skill["name"]] += 1

    print(f"\n  Unique skills: {len(skill_counter)}")
    for skill, count in skill_counter.most_common(40):
        pct = count / len(candidates) * 100
        print(f"    {skill:<45s} {count:>3d} ({pct:.0f}%)")


def explore_experience_distribution(candidates):
    
    print_section("EXPERIENCE DISTRIBUTION")

    yoe_values = [c["profile"]["years_of_experience"] for c in candidates]
    buckets = {"0-2 yrs": 0, "2-5 yrs": 0, "5-9 yrs": 0, "9-15 yrs": 0, "15+ yrs": 0}
    for y in yoe_values:
        if y < 2:
            buckets["0-2 yrs"] += 1
        elif y < 5:
            buckets["2-5 yrs"] += 1
        elif y < 9:
            buckets["5-9 yrs"] += 1
        elif y < 15:
            buckets["9-15 yrs"] += 1
        else:
            buckets["15+ yrs"] += 1

    for bucket, count in buckets.items():
        print(f"    {bucket:<15s} {count:>3d}")

    avg_yoe = sum(yoe_values) / len(yoe_values)
    print(f"\n    Average: {avg_yoe:.1f} yrs | Min: {min(yoe_values):.1f} | Max: {max(yoe_values):.1f}")


def explore_education(candidates):
    
    print_section("EDUCATION — Degree & Tier Distribution")

    degree_counter = Counter()
    tier_counter = Counter()
    field_counter = Counter()

    for cand in candidates:
        for edu in cand.get("education", []):
            degree_counter[edu.get("degree", "Unknown")] += 1
            tier_counter[edu.get("tier", "unknown")] += 1
            field_counter[edu.get("field_of_study", "Unknown")] += 1

    print(f"\n  Degree types:")
    for deg, count in degree_counter.most_common():
        print(f"    {deg:<35s} {count:>3d}")

    print(f"\n  Institution tiers:")
    for tier, count in tier_counter.most_common():
        print(f"    {tier:<35s} {count:>3d}")

    print(f"\n  Fields of study (top 15):")
    for field, count in field_counter.most_common(15):
        print(f"    {field:<35s} {count:>3d}")


def explore_engagement_activity(candidates):
    
    print_section("ENGAGEMENT & ACTIVITY ANALYSIS")

    today = date(2026, 6, 24)  # Current date as per project

    active_last_30d = 0
    active_last_90d = 0
    active_last_180d = 0
    inactive_6mo_plus = 0

    for cand in candidates:
        signals = cand.get("redrob_signals", {})
        last_active = signals.get("last_active_date", "")
        if last_active:
            try:
                last_dt = datetime.strptime(last_active, "%Y-%m-%d").date()
                days_since = (today - last_dt).days
                if days_since <= 30:
                    active_last_30d += 1
                elif days_since <= 90:
                    active_last_90d += 1
                elif days_since <= 180:
                    active_last_180d += 1
                else:
                    inactive_6mo_plus += 1
            except ValueError:
                pass

    print(f"    Active in last 30 days:   {active_last_30d:>3d}")
    print(f"    Active in 31-90 days:     {active_last_90d:>3d}")
    print(f"    Active in 91-180 days:    {active_last_180d:>3d}")
    print(f"    Inactive 180+ days:       {inactive_6mo_plus:>3d}")


def identify_ai_relevant_candidates(candidates):
    
    print_section("AI/ML-RELEVANT CANDIDATES (by title or key skills)")

    ai_titles = {"AI Engineer", "ML Engineer", "Data Scientist", "Machine Learning Engineer",
                 "Senior Machine Learning Engineer", "Junior ML Engineer", "Research Scientist",
                 "Senior AI Engineer", "Deep Learning Engineer"}

    ai_skills_must = {"Python", "sentence-transformers", "OpenAI", "BGE", "E5",
                      "Pinecone", "Weaviate", "Qdrant", "Milvus", "OpenSearch",
                      "Elasticsearch", "FAISS", "NDCG", "MRR", "MAP",
                      "embeddings", "vector database", "ranking"}
    ai_skills_nice = {"LoRA", "QLoRA", "XGBoost", "Fine-tuning LLMs",
                      "LLM fine-tuning", "learning-to-rank"}

    relevant = []
    for cand in candidates:
        title = cand["profile"]["current_title"]
        skill_names = {s["name"].lower() for s in cand.get("skills", [])}
        all_ai_skills = {s.lower() for s in ai_skills_must | ai_skills_nice}

        title_match = title in ai_titles
        matching_skills = skill_names & all_ai_skills
        has_python = "python" in skill_names

        if title_match or len(matching_skills) >= 2:
            relevant.append({
                "id": cand["candidate_id"],
                "title": title,
                "company": cand["profile"]["current_company"],
                "yoe": cand["profile"]["years_of_experience"],
                "matching_skills": matching_skills,
                "has_python": has_python,
                "title_match": title_match,
                "response_rate": cand.get("redrob_signals", {}).get("recruiter_response_rate", 0)
            })

    print(f"\n  Found {len(relevant)} potentially relevant candidates:")
    for r in relevant:
        flag = "✓ Title" if r["title_match"] else "  Skills"
        py = "PY✓" if r["has_python"] else "PY✗"
        print(f"    {r['id']} | {flag} | {r['title']:<35s} | {r['company']:<20s} | "
              f"{r['yoe']:.1f}yr | {py} | resp={r['response_rate']:.2f} | "
              f"skills: {', '.join(sorted(r['matching_skills']))}")


def detect_suspicious_candidates(candidates):
    
    print_section("SUSPICIOUS CANDIDATES (Potential Honeypots/Traps)")

    services_companies = {"TCS", "Infosys", "Wipro", "Accenture", "Cognizant",
                          "Capgemini", "HCL", "Tech Mahindra", "Mindtree",
                          "Mphasis", "LTIMindtree"}

    non_ai_titles = {"HR Manager", "Marketing Manager", "Sales Executive",
                     "Accountant", "Content Writer", "Graphic Designer",
                     "Customer Support", "Civil Engineer", "Mechanical Engineer",
                     "Operations Manager", "Project Manager"}

    ai_core_skills = {"Python", "FAISS", "Pinecone", "Weaviate", "Qdrant", "Milvus",
                      "sentence-transformers", "embeddings", "LLM", "Fine-tuning LLMs",
                      "LoRA", "XGBoost", "NLP", "RAG", "LangChain", "OpenAI",
                      "TensorFlow", "PyTorch", "Transformer", "BERT", "GPT"}

    suspects = []
    for cand in candidates:
        flags = []
        title = cand["profile"]["current_title"]
        company = cand["profile"]["current_company"]
        skill_names = {s["name"] for s in cand.get("skills", [])}
        ai_skill_count = len(skill_names & ai_core_skills)

        # Flag 1: Non-AI title with many AI skills (keyword stuffer)
        if title in non_ai_titles and ai_skill_count >= 5:
            flags.append(f"TITLE-SKILL MISMATCH: {title} with {ai_skill_count} AI skills")

        # Flag 2: Services-only company
        if company in services_companies:
            all_companies = {ch["company"] for ch in cand.get("career_history", [])}
            if all_companies.issubset(services_companies):
                flags.append(f"SERVICES-ONLY: All roles at {', '.join(all_companies)}")

        # Flag 3: Low engagement with high skills
        signals = cand.get("redrob_signals", {})
        response_rate = signals.get("recruiter_response_rate", 0)
        if ai_skill_count >= 5 and response_rate < 0.1:
            flags.append(f"LOW-ENGAGEMENT: {ai_skill_count} AI skills but {response_rate:.0%} response rate")

        if flags:
            suspects.append((cand["candidate_id"], title, company, flags))

    print(f"\n  Found {len(suspects)} suspicious candidates:")
    for cid, title, company, flags in suspects:
        print(f"\n    {cid} | {title} | {company}")
        for flag in flags:
            print(f"      ⚠️  {flag}")


def explore_career_history_depth(candidates):
    
    print_section("CAREER HISTORY DEPTH")

    role_counts = [len(c.get("career_history", [])) for c in candidates]
    avg_roles = sum(role_counts) / len(role_counts)
    print(f"    Average roles per candidate: {avg_roles:.1f}")
    print(f"    Min roles: {min(role_counts)} | Max roles: {max(role_counts)}")

    # Distribution
    dist = Counter(role_counts)
    for count in sorted(dist.keys()):
        print(f"    {count} roles: {dist[count]:>3d} candidates")


def main():
    print("\n" + "Target " * 20)
    print("  REDROB CANDIDATE DATA EXPLORATION — TASK 1")
    print("Target " * 20)

    # Load candidates
    print(f"\n  Loading candidates from: {SAMPLE_FILE}")
    candidates = load_candidates(SAMPLE_FILE)
    print(f"  Loaded {len(candidates)} candidates")

    # Run all explorations
    explore_basic_info(candidates)
    explore_title_distribution(candidates)
    explore_company_distribution(candidates)
    explore_industry_distribution(candidates)
    explore_experience_distribution(candidates)
    explore_education(candidates)
    explore_skills_distribution(candidates)
    explore_redrob_signals(candidates)
    explore_engagement_activity(candidates)
    explore_career_history_depth(candidates)
    identify_ai_relevant_candidates(candidates)
    detect_suspicious_candidates(candidates)

    # Final summary
    print_section("KEY OBSERVATIONS FOR RANKING DESIGN")
    print("""
    1. SAMPLE SUBMISSION IS A TRAP: The provided sample_submission.csv ranks
       HR Managers, Graphic Designers, Accountants at #1-#10. This is clearly
       a naive keyword-matching approach that we must NOT replicate.

    2. DATA STRUCTURE: Each candidate has 6 top-level sections:
       - profile (10 fields), career_history (array of roles),
       - education (array), skills (array with proficiency + duration),
       - certifications, languages, redrob_signals (23 behavioral signals)

    3. REDROB SIGNALS: 23 behavioral fields including:
       - Engagement: recruiter_response_rate, last_active_date, applications_submitted_30d
       - Verification: verified_email, verified_phone, linkedin_connected
       - Activity: github_activity_score, profile_views_received_30d
       - Assessment: skill_assessment_scores (dict of skill -> score 0-100)

    4. HONEYPOT INDICATORS: Title-skill mismatches, services-only backgrounds,
       low engagement with high skills, impossible experience claims.

    5. JD-RELEVANT SKILLS TO LOOK FOR:
       - MUST: embeddings, vector DB (Pinecone/Weaviate/Qdrant/Milvus/FAISS),
         ranking evaluation (NDCG/MRR/MAP), Python
       - NICE: LoRA, QLoRA, XGBoost, LLM fine-tuning
    """)

    print("\n TASK 1: Data Exploration COMPLETE\n")


if __name__ == "__main__":
    main()

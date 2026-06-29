
import json
import os
import re
from datetime import datetime, date
from collections import Counter


# Reference date for recency calculations
REFERENCE_DATE = date(2026, 6, 24)

# Services/IT body-shopping companies (red flag if ALL roles here)
SERVICES_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "hcl technologies", "tech mahindra", "mindtree", "mphasis",
    "ltimindtree", "lti", "hexaware", "persistent systems", "cyient",
    "zensar", "niit", "l&t infotech", "birlasoft", "coforge"
}

# Non-technical titles that should NOT have heavy AI/ML skills
NON_AI_TITLES = {
    "hr manager", "marketing manager", "sales executive", "accountant",
    "content writer", "graphic designer", "customer support",
    "civil engineer", "mechanical engineer", "operations manager",
    "project manager", "administrative assistant", "recruiter",
    "financial analyst", "supply chain manager", "procurement manager",
    "office manager", "executive assistant", "social media manager",
    "copywriter", "brand manager", "product marketing manager",
    "event manager", "public relations"
}

# AI/ML core skills (presence of many of these in a non-AI profile = suspect)
AI_CORE_SKILLS = {
    "python", "tensorflow", "pytorch", "keras", "scikit-learn",
    "faiss", "pinecone", "weaviate", "qdrant", "milvus", "opensearch",
    "elasticsearch", "sentence-transformers", "sentence transformers",
    "embeddings", "nlp", "llm", "fine-tuning llms", "lora", "qlora",
    "rag", "langchain", "openai", "gpt", "bert", "transformer",
    "hugging face transformers", "xgboost", "lightgbm",
    "deep learning", "machine learning", "neural networks",
    "recommendation systems", "information retrieval",
    "feature engineering", "mlflow", "mlops", "computer vision",
    "object detection", "image classification", "cnn", "rnn", "lstm",
    "gans", "reinforcement learning", "speech recognition",
    "ranking", "ndcg", "mrr", "map", "a/b testing",
    "vector database", "bentoml", "kubeflow", "weights & biases",
    "peft", "data science"
}

# AI-related titles (these should have AI skills)
AI_TITLES = {
    "ai engineer", "ml engineer", "machine learning engineer",
    "senior ai engineer", "senior machine learning engineer",
    "junior ml engineer", "data scientist", "senior data scientist",
    "deep learning engineer", "nlp engineer", "research scientist",
    "applied ml engineer", "search engineer", "recommendation systems engineer",
    "computer vision engineer", "mlops engineer"
}

# Career description keywords that suggest AI/ML production work
AI_CAREER_KEYWORDS = [
    "ranking", "recommendation", "embeddings", "retrieval", "search",
    "machine learning", "deep learning", "neural network", "nlp",
    "training", "model", "inference", "feature engineering",
    "a/b test", "ndcg", "mrr", "production ml", "deployed",
    "shipped", "pipeline", "vector", "faiss", "pinecone"
]

# Non-AI career description keywords
NON_AI_CAREER_KEYWORDS = [
    "marketing", "seo", "brand", "campaign", "advertising",
    "accounting", "bookkeeping", "tax", "audit", "financial statement",
    "sales", "crm", "lead generation", "quota", "pipeline",
    "hr", "recruitment", "hiring", "onboarding", "payroll",
    "mechanical", "cad", "solidworks", "manufacturing", "tooling",
    "civil", "construction", "structural", "concrete", "autocad",
    "graphic design", "photoshop", "illustrator", "figma", "branding",
    "content writing", "editorial", "blog", "copywriting",
    "customer support", "ticketing", "escalation", "helpdesk",
    "operations", "logistics", "warehouse", "supply chain", "inventory"
]



def detect_logical_impossibilities(candidate):
    """
    Check for logically impossible claims:
    - Skill duration > total experience
    - Career gap inconsistencies
    - Experience years don't match career history
    """
    score = 0.0
    flags = []
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0)
    yoe_months = yoe * 12
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])

    # Check 1: Skills with duration longer than total experience
    impossible_skills = 0
    for skill in skills:
        duration = skill.get("duration_months", 0)
        if duration > yoe_months + 6:  # 6 month grace for rounding
            impossible_skills += 1

    if impossible_skills > 0:
        ratio = impossible_skills / max(len(skills), 1)
        skill_score = min(ratio * 2, 1.0)  # Cap at 1.0
        score = max(score, skill_score)
        flags.append(f"IMPOSSIBLE_SKILL_DURATION: {impossible_skills} skills with duration > total experience ({yoe:.1f} yrs)")

    # Check 2: Total career duration vs claimed experience
    total_career_months = sum(ch.get("duration_months", 0) for ch in career)
    if total_career_months > 0 and yoe > 0:
        # If claimed experience is MUCH less than career duration (suspicious)
        ratio = total_career_months / (yoe_months + 1)
        if ratio > 2.0:  # Career history is 2x longer than claimed
            score = max(score, 0.4)
            flags.append(f"CAREER_DURATION_MISMATCH: career history={total_career_months}mo vs claimed={yoe_months:.0f}mo")

    # Check 3: Expert proficiency with very short duration
    for skill in skills:
        if skill.get("proficiency") == "expert" and skill.get("duration_months", 0) < 12:
            score = max(score, 0.3)
            flags.append(f"FAST_EXPERT: '{skill['name']}' expert in {skill.get('duration_months', 0)} months")
            break  # One flag is enough

    # Check 4: Too many expert/advanced skills for the experience level
    advanced_plus = sum(1 for s in skills if s.get("proficiency") in ("expert", "advanced"))
    if yoe < 3 and advanced_plus >= 5:
        score = max(score, 0.5)
        flags.append(f"TOO_MANY_EXPERT_SKILLS: {advanced_plus} advanced/expert skills with only {yoe:.1f} yrs experience")

    return score, flags


def detect_title_skill_mismatch(candidate):

    score = 0.0
    flags = []
    profile = candidate.get("profile", {})
    title = profile.get("current_title", "").lower().strip()
    skills = candidate.get("skills", [])

    skill_names_lower = {s["name"].lower() for s in skills}
    ai_skill_count = len(skill_names_lower & AI_CORE_SKILLS)

    # Check if title is non-AI
    is_non_ai_title = title in NON_AI_TITLES

    if is_non_ai_title and ai_skill_count >= 3:
        # Scale: 3 skills = 0.3, 5 = 0.5, 8+ = 0.8
        score = min(ai_skill_count * 0.1, 0.8)
        flags.append(f"TITLE_SKILL_MISMATCH: '{title}' with {ai_skill_count} AI/ML skills")

    # Extra: check if title is VERY non-technical but has expert AI skills
    very_non_tech = title in {"hr manager", "accountant", "sales executive", "content writer", "graphic designer"}
    expert_ai = sum(1 for s in skills if s.get("proficiency") == "expert" and s["name"].lower() in AI_CORE_SKILLS)

    if very_non_tech and expert_ai >= 2:
        score = max(score, 0.8)
        flags.append(f"EXPERT_AI_IN_NON_TECH: '{title}' with {expert_ai} expert-level AI skills")

    return score, flags


def detect_career_narrative_inconsistency(candidate):

    score = 0.0
    flags = []
    career = candidate.get("career_history", [])

    mismatch_count = 0
    for role in career:
        title = role.get("title", "").lower()
        description = role.get("description", "").lower()

        if not description:
            continue

        # Check if description mentions a completely different domain
        title_domain = _get_domain_from_title(title)
        desc_domain = _get_domain_from_description(description)

        if title_domain and desc_domain and title_domain != desc_domain:
            mismatch_count += 1

    if mismatch_count > 0:
        ratio = mismatch_count / max(len(career), 1)
        score = min(ratio, 0.7)
        flags.append(f"NARRATIVE_MISMATCH: {mismatch_count}/{len(career)} roles have description mismatching title")

    # Check for repeated descriptions across different roles
    descriptions = [r.get("description", "").strip() for r in career if r.get("description", "").strip()]
    if len(descriptions) >= 2:
        unique_descs = set(descriptions)
        if len(unique_descs) == 1 and len(descriptions) >= 2:
            # All descriptions are identical — lazy generation
            score = max(score, 0.3)
            flags.append(f"IDENTICAL_DESCRIPTIONS: all {len(descriptions)} role descriptions are the same text")
        elif len(unique_descs) < len(descriptions):
            dup_count = len(descriptions) - len(unique_descs)
            score = max(score, 0.2)
            flags.append(f"DUPLICATE_DESCRIPTIONS: {dup_count} repeated descriptions across roles")

    return score, flags


def _get_domain_from_title(title):

    title = title.lower()
    domain_map = {
        "engineering_ai": ["ml engineer", "ai engineer", "data scientist", "nlp engineer",
                          "deep learning", "machine learning", "research scientist"],
        "engineering_sw": ["software engineer", "backend engineer", "frontend engineer",
                          "full stack", "developer", "devops", "cloud engineer",
                          "sre", "platform engineer"],
        "marketing": ["marketing", "brand", "seo", "content", "copywriter"],
        "sales": ["sales", "account executive", "business development"],
        "hr": ["hr", "recruiter", "people", "talent"],
        "finance": ["accountant", "financial", "finance", "controller"],
        "operations": ["operations manager", "supply chain", "logistics"],
        "engineering_hw": ["mechanical engineer", "civil engineer", "electrical engineer"],
        "design": ["graphic designer", "ui/ux", "product designer"],
        "support": ["customer support", "help desk", "support engineer"],
        "management": ["project manager", "product manager", "program manager"],
        "data": ["data engineer", "data analyst", "analytics"],
    }

    for domain, keywords in domain_map.items():
        for kw in keywords:
            if kw in title:
                return domain
    return None


def _get_domain_from_description(description):
  
    desc = description.lower()

    domain_scores = {}
    domain_keywords = {
        "engineering_ai": ["machine learning", "deep learning", "neural", "model training",
                          "ml pipeline", "nlp", "embedding", "ranking model", "recommendation",
                          "transformer", "feature engineering", "inference"],
        "engineering_sw": ["api", "microservice", "backend", "frontend", "database",
                          "rest", "graphql", "deployment", "ci/cd", "git"],
        "marketing": ["marketing", "campaign", "brand", "seo", "content", "social media",
                      "advertising", "creative", "editorial", "copywriting"],
        "sales": ["sales", "quota", "crm", "lead", "pipeline", "revenue", "deal"],
        "hr": ["recruitment", "hiring", "onboarding", "payroll", "employee", "talent"],
        "finance": ["accounting", "bookkeeping", "tax", "audit", "financial", "balance sheet"],
        "operations": ["operations", "logistics", "warehouse", "fulfillment", "supply chain",
                       "inventory", "shipping"],
        "engineering_hw": ["mechanical", "cad", "solidworks", "manufacturing", "tooling",
                          "structural", "ansys", "fea", "prototype", "dfm"],
        "design": ["design", "photoshop", "illustrator", "figma", "ui", "ux",
                   "typography", "visual", "packaging"],
        "support": ["support", "ticket", "escalation", "helpdesk", "customer"],
        "data": ["data pipeline", "etl", "warehouse", "spark", "airflow", "dbt",
                 "data quality", "data engineering", "analytics"],
    }

    for domain, keywords in domain_keywords.items():
        count = sum(1 for kw in keywords if kw in desc)
        if count > 0:
            domain_scores[domain] = count

    if domain_scores:
        return max(domain_scores, key=domain_scores.get)
    return None


def detect_engagement_red_flags(candidate):

    score = 0.0
    flags = []
    signals = candidate.get("redrob_signals", {})

    # Check 1: Inactive for 6+ months
    last_active = signals.get("last_active_date", "")
    if last_active:
        try:
            last_dt = datetime.strptime(last_active, "%Y-%m-%d").date()
            days_since = (REFERENCE_DATE - last_dt).days
            if days_since > 180:
                inactivity_score = min(days_since / 365, 1.0) * 0.6
                score = max(score, inactivity_score)
                flags.append(f"INACTIVE: last active {days_since} days ago ({last_active})")
        except ValueError:
            pass

    # Check 2: Very low response rate
    response_rate = signals.get("recruiter_response_rate", 0)
    if response_rate < 0.1:
        score = max(score, 0.4)
        flags.append(f"LOW_RESPONSE_RATE: {response_rate:.0%}")

    # Check 3: High profile completeness but no applications and low engagement
    completeness = signals.get("profile_completeness_score", 0)
    applications = signals.get("applications_submitted_30d", 0)
    views = signals.get("profile_views_received_30d", 0)
    if completeness > 80 and applications == 0 and views < 3 and response_rate < 0.15:
        score = max(score, 0.5)
        flags.append(f"GHOST_PROFILE: completeness={completeness:.0f}% but 0 apps, {views} views, {response_rate:.0%} response")

    # Check 4: Not open to work (minor signal)
    if not signals.get("open_to_work_flag", True):
        score = max(score, score + 0.05)  # Minor bump

    return score, flags


def detect_services_only_background(candidate):

    score = 0.0
    flags = []
    career = candidate.get("career_history", [])

    if not career:
        return score, flags

    companies = [ch.get("company", "").lower().strip() for ch in career]
    services_count = sum(1 for c in companies if c in SERVICES_COMPANIES)

    if services_count == len(companies) and len(companies) >= 1:
        score = 0.5  # All services = moderate red flag
        if len(companies) >= 3:
            score = 0.6  # Long services-only career = stronger signal
        unique_services = set(c for c in companies if c in SERVICES_COMPANIES)
        flags.append(f"SERVICES_ONLY: all {len(companies)} roles at services companies ({', '.join(sorted(unique_services))})")
    elif services_count > 0 and services_count == len(companies) - 1:
        # Almost all services
        score = 0.3
        flags.append(f"MOSTLY_SERVICES: {services_count}/{len(companies)} roles at services companies")

    # Check industry signals too
    industries = [ch.get("industry", "").lower() for ch in career]
    if all(ind in ("it services", "consulting", "business consulting") for ind in industries if ind):
        score = max(score, 0.4)
        if "SERVICES_ONLY" not in str(flags):
            flags.append(f"ALL_IT_SERVICES_INDUSTRY: all roles in IT Services/Consulting industry")

    return score, flags


def detect_research_only_background(candidate):

    score = 0.0
    flags = []
    career = candidate.get("career_history", [])

    research_keywords = ["research", "professor", "postdoc", "phd", "academic",
                         "university", "lab", "institute", "lecturer"]
    product_keywords = ["engineer", "developer", "production", "shipped",
                        "deployed", "product", "platform", "startup"]

    research_roles = 0
    product_roles = 0

    for role in career:
        title = role.get("title", "").lower()
        description = role.get("description", "").lower()
        company = role.get("company", "").lower()

        is_research = any(kw in title or kw in company for kw in research_keywords)
        is_product = any(kw in title or kw in description for kw in product_keywords)

        if is_research:
            research_roles += 1
        if is_product:
            product_roles += 1

    if research_roles > 0 and product_roles == 0 and len(career) >= 2:
        score = 0.5
        flags.append(f"RESEARCH_ONLY: {research_roles} research roles, 0 product roles")

    return score, flags


def detect_keyword_stuffer(candidate):

    score = 0.0
    flags = []
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])

    skill_names_lower = {s["name"].lower() for s in skills}
    ai_skills = [s for s in skills if s["name"].lower() in AI_CORE_SKILLS]
    ai_skill_count = len(ai_skills)

    if ai_skill_count < 3:
        return score, flags  # Not enough AI skills to be a stuffer

    # Check 1: AI skills with 0 endorsements
    zero_endorsement_ai = sum(1 for s in ai_skills if s.get("endorsements", 0) == 0)
    if zero_endorsement_ai >= 3:
        score = max(score, 0.4)
        flags.append(f"UNENDORSED_AI_SKILLS: {zero_endorsement_ai}/{ai_skill_count} AI skills have 0 endorsements")

    # Check 2: AI skills mentioned in skills but NOT in any career description
    all_descriptions = " ".join(r.get("description", "") for r in career).lower()
    skills_not_in_career = 0
    for s in ai_skills:
        skill_name = s["name"].lower()
        # Check if skill or close variant appears in descriptions
        if skill_name not in all_descriptions and not _skill_in_text(skill_name, all_descriptions):
            skills_not_in_career += 1

    if skills_not_in_career >= 4:
        ratio = skills_not_in_career / ai_skill_count
        score = max(score, min(ratio * 0.6, 0.7))
        flags.append(f"SKILLS_NOT_IN_CAREER: {skills_not_in_career}/{ai_skill_count} AI skills never mentioned in career descriptions")

    # Check 3: Assessment scores available but very low
    signals = candidate.get("redrob_signals", {})
    assessments = signals.get("skill_assessment_scores", {})
    if assessments:
        low_scores = sum(1 for v in assessments.values() if v < 40)
        if low_scores >= 2:
            score = max(score, 0.3)
            flags.append(f"LOW_ASSESSMENT_SCORES: {low_scores} skill assessments scored below 40/100")

    return score, flags


def _skill_in_text(skill_name, text):

    # Handle multi-word skills and abbreviations
    variants = {
        "fine-tuning llms": ["fine-tun", "llm", "fine tun"],
        "sentence-transformers": ["sentence-transformer", "sentence transformer", "sbert"],
        "sentence transformers": ["sentence-transformer", "sentence transformer", "sbert"],
        "hugging face transformers": ["hugging face", "huggingface", "transformers"],
        "machine learning": ["ml", "machine learning"],
        "deep learning": ["deep learning", "dl"],
        "nlp": ["nlp", "natural language"],
        "computer vision": ["computer vision", "cv"],
        "scikit-learn": ["scikit", "sklearn"],
        "embeddings": ["embedding"],
        "recommendation systems": ["recommendation", "recommender"],
        "information retrieval": ["information retrieval", "ir"],
        "feature engineering": ["feature engineer", "feature pipeline"],
        "weights & biases": ["wandb", "weights and biases"],
        "xgboost": ["xgboost", "gradient boost"],
        "lightgbm": ["lightgbm", "light gbm"],
    }

    if skill_name in variants:
        return any(v in text for v in variants[skill_name])

    # Default: check if the skill name (or first word) appears
    return skill_name in text or skill_name.split()[0] in text if " " in skill_name else skill_name in text


def compute_honeypot_score(candidate):

    detectors = {
        "logical_impossibility": detect_logical_impossibilities,
        "title_skill_mismatch": detect_title_skill_mismatch,
        "career_narrative": detect_career_narrative_inconsistency,
        "engagement_red_flags": detect_engagement_red_flags,
        "services_only": detect_services_only_background,
        "research_only": detect_research_only_background,
        "keyword_stuffer": detect_keyword_stuffer,
    }

    # Weights for each detector (sum to ~1.0)
    weights = {
        "logical_impossibility": 0.26,
        "title_skill_mismatch": 0.28,
        "career_narrative": 0.10,
        "engagement_red_flags": 0.14,
        "services_only": 0.08,
        "research_only": 0.04,
        "keyword_stuffer": 0.10,
    }

    sub_scores = {}
    all_flags = []

    for name, detector in detectors.items():
        sub_score, flags = detector(candidate)
        sub_scores[name] = sub_score
        all_flags.extend(flags)

    # Weighted combination
    weighted_score = sum(sub_scores[name] * weights[name] for name in sub_scores)

    # Boost: if multiple detectors fire, the compound risk is higher
    active_detectors = sum(1 for s in sub_scores.values() if s > 0.15)
    if active_detectors >= 4:
        weighted_score = min(weighted_score * 1.5, 1.0)
    elif active_detectors >= 3:
        weighted_score = min(weighted_score * 1.3, 1.0)
    elif active_detectors >= 2:
        weighted_score = min(weighted_score * 1.15, 1.0)

    # Hard floor: if title-skill mismatch is very high, ensure it's flagged
    if sub_scores.get("title_skill_mismatch", 0) >= 0.7:
        weighted_score = max(weighted_score, 0.5)

    # Stronger action for clear inconsistencies and stuffing patterns
    if sub_scores.get("logical_impossibility", 0) >= 0.5 and sub_scores.get("keyword_stuffer", 0) >= 0.4:
        weighted_score = max(weighted_score, 0.42)
    if sub_scores.get("logical_impossibility", 0) >= 0.5 and sub_scores.get("career_narrative", 0) >= 0.4:
        weighted_score = max(weighted_score, 0.38)

    # Cap at 1.0
    honeypot_score = min(round(weighted_score, 4), 1.0)

    return {
        "honeypot_score": honeypot_score,
        "is_honeypot": honeypot_score >= 0.30,  # Threshold for flagging
        "flags": all_flags,
        "sub_scores": sub_scores
    }


def analyze_candidates(candidates):

    results = []
    for cand in candidates:
        result = compute_honeypot_score(cand)
        result["candidate_id"] = cand["candidate_id"]
        result["current_title"] = cand.get("profile", {}).get("current_title", "")
        result["current_company"] = cand.get("profile", {}).get("current_company", "")
        results.append(result)

    return results


def main():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file = os.path.join(script_dir, "..", "data", "sample_candidates.json")

    print("\n" + "=" * 80)
    print("  HONEYPOT & TRAP DETECTION SYSTEM — Test Run")
    print("=" * 80)

    with open(sample_file, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"\n  Loaded {len(candidates)} candidates for analysis")

    results = analyze_candidates(candidates)

    # Sort by honeypot score descending
    results.sort(key=lambda x: x["honeypot_score"], reverse=True)

    # Print all candidates with scores
    print(f"\n{'='*90}")
    print(f"  {'ID':<16s} {'Score':>6s} {'Flag':>5s}  {'Title':<30s}  {'Company':<20s}  Flags")
    print(f"{'='*90}")

    honeypot_count = 0
    for r in results:
        flag_marker = " !!!" if r["is_honeypot"] else "    "
        if r["is_honeypot"]:
            honeypot_count += 1
        flags_short = "; ".join(r["flags"][:2]) if r["flags"] else "-"
        if len(flags_short) > 60:
            flags_short = flags_short[:57] + "..."

        print(f"  {r['candidate_id']:<16s} {r['honeypot_score']:>5.3f} {flag_marker}  "
              f"{r['current_title']:<30s}  {r['current_company']:<20s}  {flags_short}")

    # Summary
    print(f"\n{'='*90}")
    print(f"  SUMMARY")
    print(f"{'='*90}")
    print(f"  Total candidates analyzed:     {len(results)}")
    print(f"  Flagged as honeypot (>= 0.30): {honeypot_count} ({honeypot_count/len(results)*100:.1f}%)")
    print(f"  Clean candidates:              {len(results) - honeypot_count}")

    # Show detailed breakdown for top flagged candidates
    print(f"\n{'='*90}")
    print(f"  TOP FLAGGED CANDIDATES — Detailed Breakdown")
    print(f"{'='*90}")

    for r in results[:10]:
        if not r["is_honeypot"]:
            continue
        print(f"\n  {r['candidate_id']} | {r['current_title']} @ {r['current_company']}")
        print(f"  Honeypot Score: {r['honeypot_score']:.3f}")
        print(f"  Sub-scores:")
        for name, sub_score in sorted(r["sub_scores"].items(), key=lambda x: x[1], reverse=True):
            bar = "#" * int(sub_score * 20)
            print(f"    {name:<25s} {sub_score:.3f} [{bar:<20s}]")
        print(f"  Flags:")
        for flag in r["flags"]:
            print(f"    - {flag}")

    print(f"\n  Honeypot detection complete.\n")


if __name__ == "__main__":
    main()

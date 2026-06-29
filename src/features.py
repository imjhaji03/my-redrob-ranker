
import re
from datetime import datetime, date


REFERENCE_DATE = date(2026, 6, 24)



MUST_HAVE_SKILLS = {
   
    "embeddings": {
        "skills": ["embeddings", "sentence-transformers", "sentence transformers",
                   "openai embeddings", "bge", "e5", "embedding models",
                   "text embeddings", "hugging face transformers"],
        "max_points": 8,
        "category": "embeddings"
    },
    
    "vector_db": {
        "skills": ["pinecone", "weaviate", "qdrant", "milvus", "opensearch",
                   "elasticsearch", "faiss", "vector database", "chromadb",
                   "pgvector"],
        "max_points": 8,
        "category": "vector_db"
    },
    
    "ranking_eval": {
        "skills": ["ndcg", "mrr", "map", "a/b testing", "ranking",
                   "information retrieval", "recommendation systems",
                   "learning-to-rank", "search relevance", "precision@k",
                   "recall@k", "ranking evaluation"],
        "max_points": 6,
        "category": "ranking_eval"
    },
    
    "python": {
        "skills": ["python"],
        "max_points": 6,
        "category": "python"
    },
}


NICE_TO_HAVE_SKILLS = {
    "llm_finetuning": {
        "skills": ["fine-tuning llms", "lora", "qlora", "peft",
                   "llm fine-tuning", "model fine-tuning", "rlhf",
                   "instruction tuning"],
        "max_points": 4,
        "category": "llm_finetuning"
    },
    "learning_to_rank": {
        "skills": ["xgboost", "lightgbm", "gradient boosting",
                   "catboost", "learning to rank", "l2r",
                   "feature engineering"],
        "max_points": 4,
        "category": "learning_to_rank"
    },
    "domain_exposure": {
        "skills": ["recommendation systems", "search", "marketplace",
                   "hr tech", "recruiting", "talent acquisition",
                   "matching", "information retrieval"],
        "max_points": 4,
        "category": "domain_exposure"
    },
}

PROFICIENCY_MULTIPLIER = {
    "expert": 1.0,
    "advanced": 0.75,
    "intermediate": 0.45,
    "beginner": 0.2,
}

# ── Company Tiers ──

TIER_1_COMPANIES = {
    # FAANG / Big Tech
    "google", "meta", "apple", "amazon", "microsoft", "netflix",
    "deepmind", "openai", "anthropic", "cohere", "stability ai",
    # Top AI labs / companies
    "nvidia", "tesla", "palantir", "databricks", "snowflake",
    "stripe", "uber", "airbnb", "linkedin", "twitter", "x",
    "salesforce", "adobe",
}

TIER_2_COMPANIES = {
    # Strong product companies (India focus)
    "swiggy", "zomato", "razorpay", "cred", "phonepe", "paytm",
    "flipkart", "meesho", "ola", "dream11", "unacademy",
    "groww", "zerodha", "byju's", "nykaa", "sharechat",
    "postman", "browserstack", "freshworks", "zoho",
    # Strong product companies (Global)
    "spotify", "shopify", "twilio", "atlassian", "hashicorp",
    "elastic", "confluent", "mongodb", "cloudflare", "datadog",
    "pied piper",
    # AI-focused startups/companies
    "mad street den", "haptik", "yellow.ai", "sarvam ai",
    "krutrim", "observe.ai",
}

TIER_3_COMPANIES = {
    # Mid-tier product companies
    "acme corp", "globex inc", "initech", "wayne enterprises",
    "stark industries", "hooli", "dunder mifflin",
    "umbrella corp",
}

SERVICES_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "hcl technologies", "tech mahindra", "mindtree", "mphasis",
    "ltimindtree", "lti", "hexaware", "persistent systems", "cyient",
    "zensar", "niit", "l&t infotech", "birlasoft", "coforge",
    "deloitte", "pwc", "kpmg", "ey", "mckinsey", "bcg", "bain",
}

# ── Career Narrative Keywords ──

CAREER_HIGH_VALUE_KEYWORDS = [
    # Ranking/recommendation/retrieval (highest value)
    "ranking model", "learning-to-rank", "learning to rank", "l2r",
    "recommendation system", "recommender", "recommendation engine",
    "search relevance", "search ranking", "retrieval system",
    "embedding-based retrieval", "semantic search", "vector search",
    "re-ranking", "reranking",
    # Evaluation
    "ndcg", "mrr", "precision@", "recall@", "a/b test", "ab test",
    "offline evaluation", "online evaluation",
    # Production ML
    "shipped", "deployed", "production ml", "production model",
    "served model", "model serving", "ml pipeline", "feature pipeline",
    "feature store", "model registry",
]

CAREER_MEDIUM_VALUE_KEYWORDS = [
    # ML/AI work
    "machine learning", "deep learning", "neural network",
    "training", "fine-tun", "inference", "model",
    "nlp", "natural language", "computer vision",
    "classification", "regression", "clustering",
    # ML infrastructure
    "ml infrastructure", "mlops", "ml platform",
    "experiment tracking", "model monitoring",
    # Data engineering (adjacent)
    "data pipeline", "feature engineering", "etl",
    "spark", "airflow", "data quality",
]

# ── AI-related titles ──

AI_TITLES_TIER_1 = {
    "recommendation systems engineer", "search engineer",
    "ranking engineer", "senior ai engineer", "ai engineer",
    "senior machine learning engineer", "machine learning engineer",
    "ml engineer", "applied ml engineer", "nlp engineer",
    "deep learning engineer", "computer vision engineer",
}

AI_TITLES_TIER_2 = {
    "data scientist", "senior data scientist", "junior ml engineer",
    "research scientist", "applied scientist", "mlops engineer",
    "ml platform engineer", "data engineer", "analytics engineer",
}

AI_TITLES_TIER_3 = {
    "software engineer", "backend engineer", "full stack developer",
    "cloud engineer", "devops engineer", "platform engineer",
    "java developer", ".net developer", "frontend engineer",
    "qa engineer", "mobile developer",
}



def compute_experience_score(candidate, max_score=30):
    """
    Map years_of_experience to a 0-30 score.

    JD says 5-9 years is ideal. We use a bell-curve-like mapping:
      - 5-9 years:  25-30 (sweet spot)
      - 3-5 years:  18-25 (good, on the way up)
      - 9-12 years: 20-25 (good, slightly past sweet spot)
      - 2-3 years:  10-18 (light experience)
      - 12-15 years: 15-20 (may be too senior / management)
      - <2 or >15:  0-15 (weak fit)
    """
    yoe = candidate.get("profile", {}).get("years_of_experience", 0)

    if yoe < 1:
        score = yoe * 5  # 0-5
    elif yoe < 2:
        score = 5 + (yoe - 1) * 7  # 5-12
    elif yoe < 3:
        score = 12 + (yoe - 2) * 6  # 12-18
    elif yoe < 5:
        score = 18 + (yoe - 3) * 3.5  # 18-25
    elif yoe <= 9:
        score = 25 + (yoe - 5) * 1.25  # 25-30
    elif yoe <= 12:
        score = 30 - (yoe - 9) * 1.67  # 30-25
    elif yoe <= 15:
        score = 25 - (yoe - 12) * 2  # 25-19
    elif yoe <= 20:
        score = 19 - (yoe - 15) * 1.5  # 19-11.5
    else:
        score = max(5, 11.5 - (yoe - 20) * 0.5)  # Diminishing

    return round(min(max(score, 0), max_score), 2)


def compute_skill_match_score(candidate, max_score=40):
    """
    Match candidate skills against JD requirements.

    Scoring:
      Must-haves (up to 28 points):
        - Embeddings (0-8), Vector DB (0-8), Ranking/eval (0-6), Python (0-6)
      Nice-to-haves (up to 12 points):
        - LLM fine-tuning (0-4), Learning-to-rank (0-4), Domain (0-4)

    For each matched skill, score depends on:
      - proficiency level (expert=1.0, advanced=0.75, intermediate=0.45, beginner=0.2)
      - duration_months (bonus for longer use)
      - endorsements (credibility signal)
    """
    skills = candidate.get("skills", [])
    skill_map = {}
    for s in skills:
        name_lower = s["name"].lower().strip()
        skill_map[name_lower] = s

    total_score = 0.0
    matched_details = {}

    # Score must-have categories
    for cat_name, cat_info in MUST_HAVE_SKILLS.items():
        cat_score = _score_skill_category(skill_map, cat_info)
        total_score += cat_score
        if cat_score > 0:
            matched_details[cat_name] = cat_score

    # Score nice-to-have categories
    for cat_name, cat_info in NICE_TO_HAVE_SKILLS.items():
        cat_score = _score_skill_category(skill_map, cat_info)
        total_score += cat_score
        if cat_score > 0:
            matched_details[cat_name] = cat_score

    # Also check career descriptions and summary for skill mentions not in skills list
    summary = candidate.get("profile", {}).get("summary", "").lower()
    career_text = " ".join(r.get("description", "") for r in candidate.get("career_history", [])).lower()
    combined_text = summary + " " + career_text

    # Bonus for mentioning critical concepts in narrative (even if not in skills list)
    narrative_bonus = 0.0
    if any(kw in combined_text for kw in ["embedding", "vector search", "semantic search"]):
        if "embeddings" not in matched_details:
            narrative_bonus += 2.0
    if any(kw in combined_text for kw in ["ranking", "retrieval", "recommendation"]):
        if "ranking_eval" not in matched_details:
            narrative_bonus += 1.5
    if "python" in combined_text and "python" not in matched_details:
        narrative_bonus += 1.0

    total_score += narrative_bonus

    return round(min(total_score, max_score), 2), matched_details


def _score_skill_category(skill_map, category_info):
    """Score a single skill category based on matched skills."""
    max_points = category_info["max_points"]
    target_skills = category_info["skills"]

    best_score = 0.0
    total_matches = 0

    for target in target_skills:
        if target in skill_map:
            s = skill_map[target]
            proficiency = s.get("proficiency", "beginner")
            duration = s.get("duration_months", 0)
            endorsements = s.get("endorsements", 0)

            # Base score from proficiency
            prof_mult = PROFICIENCY_MULTIPLIER.get(proficiency, 0.2)

            # Duration bonus (0-0.2 extra, scales with months)
            dur_bonus = min(duration / 60, 1.0) * 0.2

            # Endorsement credibility bonus (0-0.1)
            end_bonus = min(endorsements / 50, 1.0) * 0.1

            skill_score = (prof_mult + dur_bonus + end_bonus) * max_points
            best_score = max(best_score, skill_score)
            total_matches += 1

    # If multiple skills in category match, slight bonus for breadth
    if total_matches >= 2:
        best_score = min(best_score * 1.15, max_points)
    if total_matches >= 3:
        best_score = min(best_score * 1.10, max_points)  # Stacking bonus

    return round(min(best_score, max_points), 2)


def compute_company_tier_score(candidate, max_score=20):
    """
    Score based on company prestige and product-company fit.

    Considers current company AND career history companies.
    Product companies >> services companies for AI engineering roles.
    """
    career = candidate.get("career_history", [])
    current_company = candidate.get("profile", {}).get("current_company", "").lower().strip()
    current_industry = candidate.get("profile", {}).get("current_industry", "").lower().strip()

    # Score current company
    current_score = _get_company_score(current_company, current_industry)

    # Score career history — best company matters
    history_scores = []
    for role in career:
        company = role.get("company", "").lower().strip()
        industry = role.get("industry", "").lower().strip()
        history_scores.append(_get_company_score(company, industry))

    # Weighted: 60% current company, 40% best historical company
    best_history = max(history_scores) if history_scores else 0
    score = current_score * 0.6 + best_history * 0.4

    # Penalty for ALL services companies (already handled by individual scores)
    all_companies = [r.get("company", "").lower().strip() for r in career]
    all_services = all(c in SERVICES_COMPANIES for c in all_companies if c)
    if all_services and len(all_companies) >= 2:
        score *= 0.6  # Heavy penalty for services-only career

    return round(min(max(score, 0), max_score), 2)


def _get_company_score(company, industry=""):
    """Return a score (0-20) for a single company."""
    company = company.lower().strip()

    if company in TIER_1_COMPANIES:
        return 20
    elif company in TIER_2_COMPANIES:
        return 16
    elif company in TIER_3_COMPANIES:
        return 10
    elif company in SERVICES_COMPANIES:
        return 4
    else:
        # Unknown company — use industry as signal
        if "ai" in industry or "machine learning" in industry:
            return 15
        elif industry in ("technology", "software", "saas", "fintech"):
            return 12
        elif industry in ("it services", "consulting", "business consulting"):
            return 5
        else:
            return 8  # Neutral default


def compute_career_fit_score(candidate, max_score=10):
    """
    Parse career descriptions and title history to identify:
    - Shipped ranking/retrieval/recommendation systems (high value)
    - Production ML deployment experience (medium value)
    - AI-related titles (signal of domain fit)

    Returns score 0-10.
    """
    career = candidate.get("career_history", [])
    current_title = candidate.get("profile", {}).get("current_title", "").lower().strip()
    summary = candidate.get("profile", {}).get("summary", "").lower()

    score = 0.0

    # ── Title scoring ──
    if current_title in AI_TITLES_TIER_1:
        score += 3.0
    elif current_title in AI_TITLES_TIER_2:
        score += 2.0
    elif current_title in AI_TITLES_TIER_3:
        score += 0.5
    # Non-tech titles get 0

    # Historical titles bonus
    for role in career:
        title = role.get("title", "").lower().strip()
        if title in AI_TITLES_TIER_1:
            score += 1.0
        elif title in AI_TITLES_TIER_2:
            score += 0.5

    # ── Career narrative analysis ──
    all_descriptions = " ".join(r.get("description", "") for r in career).lower()
    combined_text = summary + " " + all_descriptions

    # High-value keywords (ranking, recommendation, retrieval)
    high_value_hits = sum(1 for kw in CAREER_HIGH_VALUE_KEYWORDS if kw in combined_text)
    score += min(high_value_hits * 0.5, 3.0)

    # Medium-value keywords (general ML/AI)
    medium_value_hits = sum(1 for kw in CAREER_MEDIUM_VALUE_KEYWORDS if kw in combined_text)
    score += min(medium_value_hits * 0.2, 2.0)

    # Bonus for mentioning specific achievements
    if any(phrase in combined_text for phrase in [
        "improved revenue", "improved conversion", "increased engagement",
        "reduced latency", "scaled to", "million", "production",
        "a/b test showed", "lift of", "improvement of"
    ]):
        score += 0.5

    return round(min(max(score, 0), max_score), 2)


def compute_engagement_score(candidate):

    signals = candidate.get("redrob_signals", {})

    components = []

    # 1. Response rate (weight: 0.25) — most important engagement signal
    response_rate = signals.get("recruiter_response_rate", 0)
    components.append(("response_rate", response_rate, 0.25))

    # 2. Login recency (weight: 0.20)
    last_active = signals.get("last_active_date", "")
    recency_score = 0.0
    if last_active:
        try:
            last_dt = datetime.strptime(last_active, "%Y-%m-%d").date()
            days_since = (REFERENCE_DATE - last_dt).days
            if days_since <= 7:
                recency_score = 1.0
            elif days_since <= 30:
                recency_score = 0.9
            elif days_since <= 60:
                recency_score = 0.7
            elif days_since <= 90:
                recency_score = 0.5
            elif days_since <= 180:
                recency_score = 0.3
            else:
                recency_score = max(0.1, 0.3 - (days_since - 180) / 365)
        except ValueError:
            recency_score = 0.3
    components.append(("login_recency", recency_score, 0.20))

    # 3. Open to work (weight: 0.10)
    open_to_work = 1.0 if signals.get("open_to_work_flag", False) else 0.3
    components.append(("open_to_work", open_to_work, 0.10))

    # 4. GitHub activity (weight: 0.10)
    github = signals.get("github_activity_score", -1)
    if github < 0:
        github_score = 0.3  # No GitHub linked — neutral, not a penalty
    else:
        github_score = min(github / 50, 1.0)  # Normalize to 0-1
    components.append(("github_activity", github_score, 0.10))

    # 5. Profile completeness (weight: 0.10)
    completeness = signals.get("profile_completeness_score", 50)
    completeness_score = completeness / 100
    components.append(("profile_completeness", completeness_score, 0.10))

    # 6. Applications submitted (weight: 0.10)
    apps = signals.get("applications_submitted_30d", 0)
    apps_score = min(apps / 5, 1.0)  # 5+ apps = full score
    components.append(("applications", apps_score, 0.10))

    # 7. Interview completion rate (weight: 0.10)
    interview_rate = signals.get("interview_completion_rate", 0.5)
    components.append(("interview_completion", interview_rate, 0.10))

    # 8. Saved by recruiters (weight: 0.05) — social proof
    saved = signals.get("saved_by_recruiters_30d", 0)
    saved_score = min(saved / 10, 1.0)
    components.append(("saved_by_recruiters", saved_score, 0.05))

    # Compute weighted average
    weighted_sum = sum(score * weight for _, score, weight in components)
    total_weight = sum(weight for _, _, weight in components)
    raw_score = weighted_sum / total_weight if total_weight > 0 else 0.5

    # Map to multiplier range: 0.5 to 1.2
    # raw_score is 0-1, map to 0.5-1.2
    multiplier = 0.5 + raw_score * 0.7

    return round(multiplier, 4), {name: round(val, 3) for name, val, _ in components}



def extract_all_features(candidate):

    experience_score = compute_experience_score(candidate)
    skill_match_score, skill_details = compute_skill_match_score(candidate)
    company_tier_score = compute_company_tier_score(candidate)
    career_fit_score = compute_career_fit_score(candidate)
    engagement_multiplier, engagement_details = compute_engagement_score(candidate)

    # Base score (0-100)
    base_score = experience_score + skill_match_score + company_tier_score + career_fit_score

    return {
        "candidate_id": candidate.get("candidate_id", ""),
        "experience_score": experience_score,
        "skill_match_score": skill_match_score,
        "company_tier_score": company_tier_score,
        "career_fit_score": career_fit_score,
        "base_score": round(base_score, 2),
        "engagement_multiplier": engagement_multiplier,
        "skill_details": skill_details,
        "engagement_details": engagement_details,
    }


def generate_reasoning(candidate, features, honeypot_result=None):

    profile = candidate.get("profile", {})
    title = profile.get("current_title", "Unknown")
    company = profile.get("current_company", "Unknown")
    yoe = profile.get("years_of_experience", 0)

    # Build skill match description
    skill_parts = []
    if features.get("skill_details"):
        for cat, score in sorted(features["skill_details"].items(), key=lambda x: x[1], reverse=True):
            cat_name = cat.replace("_", " ").title()
            skill_parts.append(cat_name)

    skill_str = ", ".join(skill_parts[:3]) if skill_parts else "limited AI skill match"

    # Engagement summary
    eng = features.get("engagement_multiplier", 0.5)
    if eng >= 1.0:
        eng_str = "high engagement"
    elif eng >= 0.8:
        eng_str = "moderate engagement"
    elif eng >= 0.65:
        eng_str = "low engagement"
    else:
        eng_str = "very low engagement"

    # Response rate
    resp = candidate.get("redrob_signals", {}).get("recruiter_response_rate", 0)

    # Career fit
    career_score = features.get("career_fit_score", 0)
    if career_score >= 6:
        career_str = "strong production ML/ranking experience"
    elif career_score >= 3:
        career_str = "relevant AI/ML career background"
    elif career_score >= 1:
        career_str = "some technical background"
    else:
        career_str = "non-AI career background"

    reasoning = (
        f"{title} at {company} with {yoe:.1f} yrs exp; "
        f"{career_str}; skill match: {skill_str}; "
        f"{eng_str} (resp rate {resp:.0%})"
    )

    if honeypot_result and honeypot_result.get("is_honeypot"):
        reasoning += "; ranked lower due to consistency and engagement risk signals"

    # Truncate if too long
    if len(reasoning) > 200:
        reasoning = reasoning[:197] + "..."

    return reasoning

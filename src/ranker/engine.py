from __future__ import annotations

import datetime as dt
import math
import re
from functools import lru_cache
from typing import Any, Iterable

# Terms derived from released JD and dataset schema
ROLE_TERMS = [
    "ai engineer", "ml engineer", "machine learning engineer", "applied ml",
    "applied scientist", "nlp engineer", "research engineer", "search engineer",
    "recommendation engineer", "recommendation systems", "software engineer",
    "backend engineer", "data scientist", "data engineer", "analytics engineer",
]
RETRIEVAL_TERMS = [
    "embedding", "embeddings", "retrieval", "vector search", "vector database",
    "semantic search", "hybrid search", "dense retrieval", "information retrieval",
    "faiss", "pinecone", "weaviate", "qdrant", "milvus", "pgvector",
    "elasticsearch", "opensearch", "solr", "bm25", "reranking", "ranking",
    "recommendation", "recommender", "candidate ranking",
]
LLM_ML_TERMS = [
    "llm", "large language model", "generative ai", "genai", "transformers",
    "pytorch", "tensorflow", "huggingface", "fine tuning",
    "lora", "qlora", "peft", "prompt engineering", "nlp", "machine learning",
    "deep learning", "neural network", "python", "sql",
]
PRODUCTION_TERMS = [
    "production", "deployed", "deployment", "serving", "model serving", "inference",
    "shipped", "launched", "real users", "scale", "scalable", "latency", "api",
    "monitoring", "pipeline", "distributed", "docker", "kubernetes", "mlops",
    "airflow", "mlflow", "feature store", "cloud",
]
EVALUATION_TERMS = [
    "ndcg", "mrr", "map", "offline evaluation", "online evaluation", "a b test",
    "ab test", "ranking evaluation", "retrieval quality", "regression", "benchmark",
    "precision", "recall", "experiment",
]
PRODUCT_TERMS = [
    "product", "startup", "saas", "fintech", "e commerce", "marketplace", "consumer",
    "platform", "user", "recruiting", "hr tech", "talent",
]
ANTI_DOMAIN_TERMS = [
    "accountant", "civil engineer", "graphic designer", "hr manager", "content writer",
    "sales executive", "marketing manager", "business analyst", "operations manager",
    "customer support", "project manager", "teacher", "lawyer", "doctor", "architect",
    "finance manager", "recruiter", "receptionist", "administrative", "secretary",
    "janitor", "driver",
]
VISION_SPEECH_TERMS = [
    "computer vision", "image classification", "object detection", "opencv", "speech",
    "speech recognition", "asr", "tts", "robotics", "robotic",
]
SERVICE_COMPANIES = [
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "hcl",
    "tech mahindra", "mphasis", "hexaware", "mindtree", "l t infotech",
    "ltimindtree", "niit technologies", "persistent",
]
PRODUCT_INDUSTRIES = {
    "software", "saas", "fintech", "e commerce", "food delivery", "edtech",
    "ai ml", "adtech", "marketplace", "internet", "consumer technology",
}
PREFERRED_LOCATIONS = {"pune", "noida", "delhi", "delhi ncr", "mumbai", "hyderabad"}


def normalize_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


@lru_cache(maxsize=512)
def term_pattern(term: str) -> re.Pattern[str]:
    normalized = normalize_text(term)
    return re.compile(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])")


def has_term(normalized_text: str, term: str) -> bool:
    return bool(term_pattern(term).search(normalized_text))


def matching_terms(normalized_text: str, terms: Iterable[str]) -> list[str]:
    return [term for term in terms if has_term(normalized_text, term)]


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value not in (None, "", "null") else default
    except (TypeError, ValueError):
        return default


def parse_date(value: Any) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def current_role(candidate: dict[str, Any]) -> dict[str, Any]:
    roles = candidate.get("career_history", []) or []
    if not roles:
        return {}
    current = [role for role in roles if role.get("is_current")]
    pool = current or roles
    return max(pool, key=lambda role: parse_date(role.get("start_date")) or dt.date.min)


def all_profile_text(candidate: dict[str, Any]) -> str:
    profile = candidate.get("profile", {}) or {}
    parts = [
        profile.get("headline", ""), profile.get("summary", ""),
        profile.get("current_title", ""), profile.get("current_company", ""),
        profile.get("current_industry", ""), profile.get("location", ""),
        profile.get("country", ""),
    ]
    for role in candidate.get("career_history", []) or []:
        parts.extend([role.get("company", ""), role.get("title", ""), role.get("industry", ""), role.get("description", "")])
    for skill in candidate.get("skills", []) or []:
        parts.extend([skill.get("name", ""), skill.get("proficiency", "")])
    for education in candidate.get("education", []) or []:
        parts.extend([education.get("institution", ""), education.get("degree", ""), education.get("field_of_study", "")])
    for certification in candidate.get("certifications", []) or []:
        parts.extend([certification.get("name", ""), certification.get("issuer", "")])
    return normalize_text(" ".join(str(part) for part in parts))


def career_text(candidate: dict[str, Any]) -> str:
    return normalize_text(" ".join(
        f"{role.get('title', '')} {role.get('industry', '')} {role.get('description', '')}"
        for role in candidate.get("career_history", []) or []
    ))


def skills_text(candidate: dict[str, Any]) -> str:
    return normalize_text(" ".join(
        f"{skill.get('name', '')} {skill.get('proficiency', '')}"
        for skill in candidate.get("skills", []) or []
    ))


def is_disqualified(candidate: dict[str, Any]) -> bool:
    title = normalize_text((candidate.get("profile", {}) or {}).get("current_title", ""))
    return any(has_term(title, term) for term in ANTI_DOMAIN_TERMS)


def experience_score(years: float) -> float:
    if years <= 0:
        return 0.0
    if 6.0 <= years <= 8.0:
        return 5.0
    if 5.0 <= years < 6.0:
        return 4.0 + (years - 5.0)
    if 8.0 < years <= 9.0:
        return 5.0 - (years - 8.0) * 0.7
    if years < 5.0:
        return max(0.5, years * 0.75)
    return max(0.4, 4.3 - (years - 9.0) * 0.45)


def normalized_ratio(value: Any, maximum: float) -> float:
    return max(0.0, min(safe_float(value, 0.0) / maximum, 1.0))


def skill_quality(candidate: dict[str, Any], relevant_skill_names: set[str]) -> tuple[float, int]:
    signals = candidate.get("redrob_signals", {}) or {}
    assessments = {normalize_text(k): safe_float(v, 0.0) / 100.0 for k, v in (signals.get("skill_assessment_scores", {}) or {}).items()}
    score = 0.0
    suspicious = 0
    for skill in candidate.get("skills", []) or []:
        name = normalize_text(skill.get("name", ""))
        if not name or not any(has_term(name, term) for term in relevant_skill_names):
            continue
        proficiency = {"beginner": 0.15, "intermediate": 0.35, "advanced": 0.65, "expert": 0.9}.get(
            normalize_text(skill.get("proficiency", "")), 0.0
        )
        duration = safe_float(skill.get("duration_months"), 0.0)
        endorsement = min(safe_float(skill.get("endorsements"), 0.0) / 50.0, 1.0)
        assessment = assessments.get(name, 0.0)
        if proficiency >= 0.85 and duration <= 0:
            suspicious += 1
        score += 0.45 * proficiency + 0.25 * min(duration / 36.0, 1.0) + 0.15 * endorsement + 0.15 * assessment
    return min(score, 8.0), suspicious


def product_tilt(candidate: dict[str, Any]) -> float:
    roles = candidate.get("career_history", []) or []
    if not roles:
        return 0.0
    service = 0
    product = 0
    for role in roles:
        company = normalize_text(role.get("company", ""))
        industry = normalize_text(role.get("industry", ""))
        if any(has_term(company, term) for term in SERVICE_COMPANIES) or industry == "it services":
            service += 1
        if industry in PRODUCT_INDUSTRIES:
            product += 1
    if not roles:
        return 0.0
    ratio = service / len(roles)
    if product > 0:
        return 0.8 * (1.0 - ratio)
    if service == len(roles):
        return -1.2
    return 0.0


def behavior_features(candidate: dict[str, Any], as_of: dt.date) -> dict[str, float]:
    signals = candidate.get("redrob_signals", {}) or {}
    active_date = parse_date(signals.get("last_active_date"))
    inactive_days = max(0, (as_of - active_date).days) if active_date else 365
    recency = max(0.0, 1.0 - min(inactive_days, 365) / 365.0)
    response = max(0.0, min(safe_float(signals.get("recruiter_response_rate"), 0.0), 1.0))
    interview = max(0.0, min(safe_float(signals.get("interview_completion_rate"), 0.0), 1.0))
    completeness = normalized_ratio(signals.get("profile_completeness_score"), 100.0)
    github = 0.0 if safe_float(signals.get("github_activity_score"), -1.0) < 0 else normalized_ratio(signals.get("github_activity_score"), 100.0)
    search = min(math.log1p(safe_float(signals.get("search_appearance_30d"), 0.0)) / math.log1p(250.0), 1.0)
    saved = min(math.log1p(safe_float(signals.get("saved_by_recruiters_30d"), 0.0)) / math.log1p(20.0), 1.0)
    verified = (int(bool(signals.get("verified_email"))) + int(bool(signals.get("verified_phone"))) + int(bool(signals.get("linkedin_connected")))) / 3.0
    open_to_work = 1.0 if signals.get("open_to_work_flag") else 0.0
    notice = max(0.0, 1.0 - min(safe_float(signals.get("notice_period_days"), 180.0), 90.0) / 90.0)
    activity = 0.30 * recency + 0.22 * response + 0.12 * interview + 0.10 * completeness + 0.08 * github + 0.06 * search + 0.04 * saved + 0.04 * verified + 0.04 * open_to_work
    return {
        "recency": recency, "inactive_days": float(inactive_days), "response": response,
        "interview": interview, "completeness": completeness, "github": github,
        "search": search, "saved": saved, "verified": verified, "open_to_work": open_to_work,
        "notice": notice, "activity": activity,
    }


def location_score(candidate: dict[str, Any]) -> float:
    profile = candidate.get("profile", {}) or {}
    location = normalize_text(profile.get("location", ""))
    country = normalize_text(profile.get("country", ""))
    signals = candidate.get("redrob_signals", {}) or {}
    if country != "india":
        return 0.0
    if any(has_term(location, place) for place in PREFERRED_LOCATIONS):
        return 0.65
    if signals.get("willing_to_relocate"):
        return 0.45
    return 0.15


def score_candidate(candidate: dict[str, Any], as_of: dt.date) -> tuple[float, dict[str, Any]]:
    profile = candidate.get("profile", {}) or {}
    latest = current_role(candidate)
    full_text = all_profile_text(candidate)
    career = career_text(candidate)
    title = normalize_text(profile.get("current_title", ""))
    latest_text = normalize_text(f"{latest.get('title', '')} {latest.get('description', '')}")

    role_hits = matching_terms(title, ROLE_TERMS)
    retrieval_career = matching_terms(career, RETRIEVAL_TERMS)
    ml_career = matching_terms(career, LLM_ML_TERMS)
    production_hits = matching_terms(career, PRODUCTION_TERMS)
    evaluation_hits = matching_terms(career, EVALUATION_TERMS)
    product_hits = matching_terms(career, PRODUCT_TERMS)
    vision_hits = matching_terms(full_text, VISION_SPEECH_TERMS)
    relevant_skill_names = set(RETRIEVAL_TERMS + LLM_ML_TERMS + ["python", "sql"])
    skill_score, suspicious_skills = skill_quality(candidate, relevant_skill_names)

    title_score = min(len(role_hits), 3) * 2.0
    retrieval_score = min(len(retrieval_career), 7) * 1.35
    ml_score = min(len(ml_career), 7) * 0.75
    production_score = min(len(production_hits), 5) * 0.85
    evaluation_score = min(len(evaluation_hits), 4) * 0.75
    python_score = 0.8 if has_term(full_text, "python") else 0.0
    skill_context_score = min(len(matching_terms(full_text, RETRIEVAL_TERMS)) + len(ml_career), 10) * 0.25
    fit_score = title_score + retrieval_score + ml_score + production_score + evaluation_score + python_score + skill_context_score + skill_score

    years = safe_float(profile.get("years_of_experience"), 0.0)
    exp_score = experience_score(years)
    behavior = behavior_features(candidate, as_of)
    behavior_modifier = 0.58 + 0.42 * behavior["activity"]
    notice_score = behavior["notice"] * 0.65
    loc_score = location_score(candidate)
    product_score = product_tilt(candidate)

    recent_coding = len(matching_terms(latest_text, PRODUCTION_TERMS))
    recent_technical = len(matching_terms(latest_text, RETRIEVAL_TERMS + LLM_ML_TERMS))
    career_months = sum(int(safe_float(role.get("duration_months"), 0.0)) for role in candidate.get("career_history", []) or [])
    short_roles = sum(1 for role in candidate.get("career_history", []) or [] if safe_float(role.get("duration_months"), 0.0) < 18)
    role_churn_penalty = 0.7 if len(candidate.get("career_history", []) or []) >= 4 and short_roles >= 2 else 0.0
    trust_penalty = min(suspicious_skills * 0.5, 1.5)
    history_gap_penalty = 0.8 if years >= 6 and career_months < 24 else 0.0
    research_only_penalty = 1.0 if has_term(career, "research scientist") and not production_hits else 0.0
    vision_only_penalty = 1.2 if len(vision_hits) >= 2 and not retrieval_career and not ml_career else 0.0
    framework_only_penalty = 0.7 if has_term(full_text, "langchain") and len(production_hits) == 0 and len(retrieval_career) <= 1 else 0.0
    current_role_penalty = 1.0 if recent_technical == 0 and len(role_hits) == 0 else 0.0

    raw_score = (
        fit_score * behavior_modifier
        + exp_score
        + product_score
        + notice_score
        + loc_score
        + 0.7 * min(recent_coding, 4)
        - role_churn_penalty
        - trust_penalty
        - history_gap_penalty
        - research_only_penalty
        - vision_only_penalty
        - framework_only_penalty
        - current_role_penalty
    )
    
    evidence = []
    for label, terms in (("retrieval/ranking", retrieval_career), ("ML/LLM", ml_career), ("production", production_hits), ("evaluation", evaluation_hits)):
        if terms:
            evidence.append(label)
    
    skills_names = [str(skill.get("name", "")).strip() for skill in candidate.get("skills", []) if skill.get("name")]
    matched_skill_names = [s for s in skills_names if any(has_term(normalize_text(s), t) for t in relevant_skill_names)]
    
    concerns = []
    if behavior["inactive_days"] > 120:
        concerns.append(f"last active {int(behavior['inactive_days'])} days before cutoff")
    if behavior["response"] < 0.2:
        concerns.append(f"recruiter response {behavior['response']:.0%}")
    if safe_float((candidate.get("redrob_signals", {}) or {}).get("notice_period_days"), 180) > 30:
        concerns.append(f"notice {int(safe_float((candidate.get('redrob_signals', {}) or {}).get('notice_period_days'), 180))}d")
    if product_score < 0:
        concerns.append("consulting-heavy career history")
    if suspicious_skills:
        concerns.append("some expert skills have no stated duration")
    if not concerns:
        concerns.append("no major availability concern")

    features = {
        "raw_score": round(raw_score, 8),
        "fit_score": round(fit_score, 4),
        "experience_score": round(exp_score, 4),
        "behavior_modifier": round(behavior_modifier, 4),
        "behavior_activity": round(behavior["activity"], 4),
        "evidence": evidence,
        "matched_skills": matched_skill_names,
        "concerns": concerns,
        "title": str(profile.get("current_title", "")).strip() or "Unknown title",
        "years": years,
        "notice_days": int(safe_float((candidate.get("redrob_signals", {}) or {}).get("notice_period_days"), 180)),
        "response": behavior["response"],
        "inactive_days": int(behavior["inactive_days"]),
    }
    
    return round(raw_score, 8), features

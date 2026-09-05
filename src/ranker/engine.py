from __future__ import annotations
import datetime as dt
import math
import re
from functools import lru_cache
from typing import Any, Iterable

ROLE_TERMS = ["ai engineer", "ml engineer", "machine learning engineer", "applied ml", "applied scientist", "nlp engineer", "research engineer", "search engineer", "recommendation engineer", "software engineer", "backend engineer", "data scientist", "data engineer"]
AI_TERMS = ["ai", "ml", "machine learning", "deep learning", "llm", "genai", "generative ai", "nlp", "python", "pytorch", "tensorflow", "transformers", "huggingface", "fine tuning", "lora", "qlora", "peft", "prompt engineering", "rag", "retrieval", "embedding", "embeddings", "vector search", "vector database", "semantic search", "faiss", "pinecone", "weaviate", "qdrant", "milvus", "pgvector", "elasticsearch", "opensearch", "bm25", "reranking", "ranking", "recommendation", "fastapi", "docker", "kubernetes", "mlops", "mlflow", "airflow", "model serving", "inference", "evaluation", "precision", "recall", "ndcg", "mrr", "map"]
ANTI_DOMAIN_TERMS = ["accountant", "civil engineer", "graphic designer", "hr manager", "content writer", "sales executive", "sales manager", "marketing manager", "business analyst", "operations manager", "customer support", "project manager", "teacher", "lawyer", "doctor", "architect", "finance manager", "recruiter", "receptionist", "administrative", "secretary", "janitor", "driver", "business development", "human resources", "talent acquisition", "procurement", "legal counsel"]
SERVICE_INDUSTRIES = {"it services", "outsourcing", "bpo", "consulting", "staffing", "business process management"}
PRODUCT_INDUSTRIES = {"technology", "saas", "artificial intelligence", "machine learning", "research", "internet", "software", "software products", "fintech", "edtech", "healthtech", "e commerce", "marketplace"}
VARIANTS = {"hugging face": "huggingface", "hf transformers": "huggingface", "lang chain": "langchain", "llama index": "llamaindex", "open ai": "openai", "weights and biases": "wandb", "weights biases": "wandb", "scikit learn": "scikitlearn", "gpt 4": "gpt4", "chroma db": "chromadb"}
PROFICIENCY = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.75, "expert": 1.0}

def normalize_text(value: Any) -> str:
    text = re.sub(r"[^a-z0-9+#.-]+", " ", str(value or "").lower()).strip()
    for old, new in VARIANTS.items(): text = text.replace(old, new)
    return re.sub(r"\s+", " ", text)

@lru_cache(maxsize=1024)
def term_pattern(term: str) -> re.Pattern[str]: return re.compile(rf"(?<![a-z0-9]){re.escape(normalize_text(term))}(?![a-z0-9])")
def has_term(text: str, term: str) -> bool: return bool(term_pattern(term).search(normalize_text(text)))
def safe_float(value: Any, default: float = 0.0) -> float:
    try: return float(value) if value not in (None, "", "null") else default
    except (TypeError, ValueError): return default
def profile(c): return c.get("profile", {}) or {}
def signals(c): return c.get("redrob_signals", {}) or {}
def candidate_id(c): return str(c.get("candidate_id") or profile(c).get("candidate_id") or "")
def parse_date(value):
    try: return dt.date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError): return None

def full_text(c):
    p = profile(c); parts = [p.get(k, "") for k in ("current_title", "headline", "summary", "current_industry", "location")]
    for r in c.get("career_history", []) or []: parts += [r.get("title", ""), r.get("description", ""), r.get("industry", "")]
    for s in c.get("skills", []) or []: parts += [s.get("name", ""), s.get("proficiency", "")]
    for x in c.get("certifications", []) or []: parts += [x.get("name", ""), x.get("issuer", "")]
    return normalize_text(" ".join(map(str, parts)))

def is_disqualified(c): return any(has_term(profile(c).get("current_title", ""), t) for t in ANTI_DOMAIN_TERMS)

def experience_score(years):
    points = [(0, 0.0), (1, 1.0), (3, 3.8), (5, 6.0), (7, 6.2), (9, 5.8), (12, 4.5), (16, 3.0), (20, 1.5)]
    y = max(0.0, years)
    if y >= 20: return 0.8
    for (x1, v1), (x2, v2) in zip(points, points[1:]):
        if x1 <= y <= x2: return v1 + (v2-v1) * (y-x1)/(x2-x1)
    return 0.0

def weighted_skills(c):
    total, matched = 0.0, []
    for s in c.get("skills", []) or []:
        name = normalize_text(s.get("name", ""))
        if not name or not any(has_term(name, t) for t in AI_TERMS): continue
        prof = PROFICIENCY.get(normalize_text(s.get("proficiency", "")), 0.0)
        duration = min(math.log1p(max(0.0, safe_float(s.get("duration_months"))))/math.log1p(60), 1.0)
        endorse = min(math.log1p(max(0.0, safe_float(s.get("endorsements"))))/math.log1p(50), 1.0)
        points = prof * (0.5 + 0.3*duration + 0.2*endorse); total += points
        matched.append({"name": s.get("name", name), "proficiency": s.get("proficiency", "unknown"), "duration_months": int(safe_float(s.get("duration_months"))), "points": points})
    return min(total*2.4, 8.0), sorted(matched, key=lambda x: (-x["points"], x["name"]))

def assessment_score(c):
    vals = [safe_float(v) for k,v in signals(c).get("skill_assessment_scores", {}).items() if any(has_term(k,t) for t in AI_TERMS)]
    return min(sum(v/100*0.4 for v in vals), 3.0), (sum(vals)/len(vals) if vals else 0.0)

def availability_score(c):
    s = signals(c); notice = safe_float(s.get("notice_period_days"), 180); response = max(0,min(safe_float(s.get("recruiter_response_rate")),1)); hours = safe_float(s.get("avg_response_time_hours"),999)
    notice_points = 2.0 if notice <= 15 else 1.5 if notice <= 30 else 0.8 if notice <= 60 else 0.0
    speed = 1.0 if hours < 4 else 0.5 if hours < 24 else 0.0 if hours < 72 else -0.5
    interview = max(0,min(safe_float(s.get("interview_completion_rate")),1))*1.5; offer = safe_float(s.get("offer_acceptance_rate"),-1); offer_points = 0.5 if offer < 0 else 0.5+max(0,min(offer,1)); open_points = 1.0 if s.get("open_to_work_flag") else 0.0
    score = max(0, notice_points + response*1.5 + speed + interview + offer_points + open_points)
    return min(score,8.0), {"response": response, "notice_days": notice, "interview": interview}

def product_tilt(c):
    total = service = product = 0.0
    for r in c.get("career_history", []) or []:
        w = max(1.0, safe_float(r.get("duration_months"),1)); industry = normalize_text(r.get("industry", "")); total += w
        if industry in SERVICE_INDUSTRIES: service += w
        if industry in PRODUCT_INDUSTRIES: product += w
    if not total: return 0.0
    return max(-1.0, min(2.0, 2.0-(service/total)*2.5+min(product/total,1)*0.5))

def score_candidate(c, as_of: dt.date, bm25_points=0.0):
    p, s = profile(c), signals(c); skills, matched = weighted_skills(c); assessment, assessment_avg = assessment_score(c); availability, behavior = availability_score(c)
    github = 0.0 if safe_float(s.get("github_activity_score"),-1) < 0 else safe_float(s.get("github_activity_score"))/100*2
    tiers = {"tier_1":1.0,"tier_2":0.5,"tier_3":0.0,"tier_4":-0.2,"unknown":0.0}; edu_tier = next((str(e.get("tier","unknown")).lower() for e in c.get("education",[]) or [] if e.get("tier")),"unknown"); edu = tiers.get(edu_tier,0)
    last = parse_date(s.get("last_active_date")); inactive = (as_of-last).days if last else 365; recency = max(0,3*(1-min(max(inactive,0),365)/365))
    demand = min(math.log1p(max(0,safe_float(s.get("saved_by_recruiters_30d")))*0.5),2); cert_terms = ("tensorflow","google ml","aws ml","deeplearning","coursera","fast ai","huggingface","machine learning","ai")
    cert = min(0.3*sum(any(has_term(f"{x.get('name','')} {x.get('issuer','')}",t) for t in cert_terms) for x in c.get("certifications",[]) or []),1.5); complete = min(max(safe_float(s.get("profile_completeness_score")),0)/100,1)
    text = full_text(c); co = 2.0 if has_term(text,"rag") and (has_term(text,"deploy") or has_term(text,"production")) else 0.0; co += 2.0 if has_term(text,"llm") and has_term(text,"fine tuning") and has_term(text,"production") else 0.0
    tilt = product_tilt(c); years = safe_float(p.get("years_of_experience")); raw = bm25_points+skills+assessment+experience_score(years)+availability+github+edu+tilt+recency+demand+cert+complete+co
    features = {"title":p.get("current_title","") or "Unknown title","years":years,"matched_skills":matched,"assessment_avg":assessment_avg,"response":behavior["response"],"notice_days":behavior["notice_days"],"interview":behavior["interview"],"github":github,"education_tier":edu_tier,"product_tilt":tilt,"raw_score":raw}
    return round(raw,8), features

def normalise_scores(entries):
    ordered = sorted(entries,key=lambda x:(-x[0],x[1]));
    if not ordered: return []
    high, low = ordered[0][0], ordered[-1][0]; span = high-low
    return [(raw,cid,cand,feat,1.0 if span==0 else (raw-low)/span) for raw,cid,cand,feat in ordered]

def build_reasoning(c, f, rank, norm):
    skills = ", ".join(f"{x['name']} ({x['proficiency']}, {x['duration_months']}mo)" for x in f["matched_skills"][:3]) or "limited named AI/ML skills"; github = "no GitHub" if f["github"]==0 else f"{f['github']/2*100:.0f}/100 GitHub"; notice = "Immediate" if f["notice_days"]<=0 else f"{f['notice_days']:.0f}d notice"; tilt = "Product background" if f["product_tilt"]>0.5 else "Services background" if f["product_tilt"]<-.3 else "Mixed background"
    options = [f"{f['title']} | {f['years']:.1f}yr | Skills: {skills} | retrieval/ranking evidence | Assessment avg: {f['assessment_avg']:.0f}/100 | {notice} | GitHub: {github} | Score: {norm:.4f}", f"{notice} | {f['years']:.1f}yr [{f['title']}] | {skills} | Recruiter response: {f['response']:.0%} | Interview rate: {f['interview']/1.5:.0%} | Score: {norm:.4f}", f"{f['years']:.1f}yr [{f['title']}] | {skills} | {f['education_tier']} | {tilt} | {notice} | retrieval/ranking evidence | Score: {norm:.4f}"]
    return options[int(re.sub(r"\D","",candidate_id(c)) or "0")%3]

def iter_candidates(path) -> Iterable[dict[str,Any]]:
    import json
    with open(path,encoding="utf-8") as h:
        for line in h:
            if line.strip(): yield json.loads(line)

def discover_as_of(path):
    latest = None
    for c in iter_candidates(path):
        d = parse_date(signals(c).get("last_active_date"))
        if d and (latest is None or d>latest): latest=d
    return latest or dt.date(2026,5,31)

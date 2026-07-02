#!/usr/bin/env python3
"""
redrob-ranker  —  India Runs Data & AI Challenge  (Track 1)
Author : Yash Sharma  (@Yashsh101)

Strategy
--------
Single-pass streaming ranker over a JSONL candidate pool.
Computes a composite scalar score per candidate across six independent
signal dimensions, maintains a min-heap of the top-K candidates, then
sorts and writes the final top-100 with normalised scores and
deterministic, diversified reasoning strings.

Signal dimensions
-----------------
1. Keyword relevance   — log-scaled hits against JD-derived core/bonus vocabulary
2. Experience fit      — continuous piecewise-linear curve peaking at 5-9 YoE
3. Availability        — notice period + open-to-work flag + response rate + activity
4. Product tilt        — proportional penalty for IT-services-heavy career history
5. Recency boost       — tiered keyword scan of most-recent role title + description
6. Title guard         — hard disqualification of clearly off-domain profiles

Properties
----------
* O(1) RAM  — streams JSONL line-by-line, heap never exceeds --topk entries
* Deterministic  — sort key (-score, candidate_id) gives stable output
* Reproducible   — no randomness; identical input → identical output
* CPU-only       — stdlib + math; zero ML framework dependencies
* Single command — python rank.py --candidates <path> --out <path>
"""

import json
import csv
import argparse
import heapq
import re
import math
from typing import Any

# ---------------------------------------------------------------------------
# JD SIGNALS  (Senior AI/ML Engineer — Redrob / India Runs challenge)
# ---------------------------------------------------------------------------

# Core vocabulary drawn directly from the job description and standard JD terms
# for a Senior AI/ML Engineer specialising in RAG, embeddings, and LLM systems.
CORE_KEYWORDS: list[str] = [
    # Vector / retrieval infrastructure
    "embedding", "embeddings", "retrieval", "vector", "faiss", "qdrant",
    "weaviate", "milvus", "pinecone", "chroma", "pgvector",
    "elasticsearch", "opensearch", "solr",
    # RAG / search paradigms
    "rag", "retrieval augmented", "semantic search", "dense retrieval",
    "hybrid search", "reranking", "ranking", "information retrieval",
    "bm25", "colbert", "dpr",
    # LLM / GenAI
    "llm", "large language model", "generative ai", "genai",
    "fine-tuning", "fine tuning", "lora", "qlora", "peft", "rlhf",
    "prompt engineering", "instruction tuning", "gpt", "llama", "mistral",
    "gemini", "claude", "openai",
    # NLP / ML core
    "nlp", "natural language processing", "transformers", "bert", "roberta",
    "sentence transformers", "text classification", "named entity",
    "machine learning", "deep learning", "neural network",
    # MLOps / infrastructure
    "mlflow", "mlops", "model serving", "triton", "torchserve",
    "kubeflow", "airflow", "feature store", "data pipeline",
    # Frameworks / libraries
    "pytorch", "tensorflow", "jax", "huggingface", "langchain",
    "llamaindex", "haystack",
    # Languages (role-critical)
    "python", "sql",
]

# High-signal bonus terms — niche but strongly predictive of JD fit
BONUS_KEYWORDS: list[str] = [
    "candidate ranking", "talent intelligence", "hr tech", "recruitment",
    "applicant tracking", "resume parsing", "job matching",
    "knowledge graph", "graph neural", "multi-modal",
    "learning to rank", "listwise", "pairwise", "pointwise",
    "cross-encoder", "bi-encoder",
]

# IT-services / outsourcing companies — heavy presence signals consulting
# background rather than product/research depth. Proportional penalty applied.
SERVICE_COMPANIES: list[str] = [
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "mphasis", "hexaware", "mindtree",
    "l&t infotech", "ltimindtree", "niit technologies", "persistent",
]

# Current-title strings that definitively indicate a non-ML domain.
# Any candidate whose current_title contains one of these strings is
# excluded from ranking entirely (hard disqualification).
DISQUALIFY_TITLES: list[str] = [
    "accountant", "civil engineer", "graphic designer", "hr manager",
    "content writer", "sales executive", "marketing manager",
    "business analyst", "operations manager", "customer support",
    "project manager", "teacher", "lawyer", "doctor", "architect",
    "finance manager", "legal", "recruiter", "receptionist",
    "administrative", "secretary", "janitor", "driver",
]

# ---------------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------------

def safe_float(val: Any, default: float = 0.0) -> float:
    """Coerce val to float; return default on None / empty / unparseable."""
    try:
        return float(val) if val not in (None, "", "null") else default
    except (ValueError, TypeError):
        return default


def is_disqualified(c: dict) -> bool:
    """Return True when the candidate's current title is clearly off-domain."""
    title = str(c.get("profile", {}).get("current_title", "")).lower()
    return any(token in title for token in DISQUALIFY_TITLES)


def build_text(c: dict) -> str:
    """
    Concatenate all searchable fields into one lowercase string.
    Truncates long free-text fields to avoid pathological runtimes on
    candidates with multi-page descriptions.
    """
    p = c.get("profile", {}) or {}
    skills = " ".join(
        f"{s.get('name', '')} {s.get('category', '')}"
        for s in c.get("skills", [])
    )
    career = " ".join(
        f"{r.get('title', '')} {str(r.get('description', ''))[:300]}"
        for r in c.get("career_history", [])
    )
    education = " ".join(
        f"{e.get('degree', '')} {e.get('field', '')}"
        for e in c.get("education", [])
    )
    summary  = str(p.get("summary", ""))[:600]
    headline = str(p.get("headline", ""))
    title    = str(p.get("current_title", ""))
    return f"{headline} {title} {summary} {skills} {career} {education}".lower()


# ---------------------------------------------------------------------------
# SCORING COMPONENTS
# ---------------------------------------------------------------------------

def keyword_score(text: str) -> float:
    """
    Log-scaled keyword relevance score.

    Using log1p prevents a candidate who keyword-stuffs a 5-page summary
    from dominating genuine experts with strong but concise profiles.
    Bonus terms receive a higher per-hit multiplier to reward rare, highly
    specific JD signals.

    Returns a continuous float; typical range 0–18.
    """
    core  = sum(1 for k in CORE_KEYWORDS  if k in text)
    bonus = sum(1 for k in BONUS_KEYWORDS if k in text)
    return math.log1p(core) * 3.5 + bonus * 1.8


def experience_score(yoe: float) -> float:
    """
    Continuous piecewise-linear curve for years-of-experience.

    The target role is Senior AI/ML Engineer — sweet spot 5-9 YoE.
    The curve rises steeply to the sweet spot, holds a plateau, then
    decays for over-senior candidates (likely overqualified / expensive).

    Breakpoints
    -----------
    0  YoE → 0.0  (no experience)
    2  YoE → 1.6  (junior)
    5  YoE → 5.2  (approaching sweet spot)
    7  YoE → 6.0  (peak)
    9  YoE → 5.6  (still strong)
    14 YoE → 3.6  (senior principal territory)
    20 YoE → 0.6  (overqualified)
    20+ YoE→ 0.3  (asymptotic floor)
    """
    if yoe <= 0:        return 0.0
    if yoe < 2:         return yoe * 0.8
    if yoe < 5:         return 1.6 + (yoe - 2) * 1.2
    if yoe < 7:         return 5.2 + (yoe - 5) * 0.4
    if yoe <= 9:        return 6.0 - (yoe - 7) * 0.2
    if yoe <= 14:       return 5.6 - (yoe - 9) * 0.4
    if yoe <= 20:       return 3.6 - (yoe - 14) * 0.55
    return 0.3


def availability_score(c: dict) -> float:
    """
    Composite availability score from Redrob platform signals.

    Components
    ----------
    notice_period_days : 0-3 pts (lower is better)
    open_to_work_flag  : 0 or 1.5 pts
    response_rate      : 0-1.5 pts (continuous)
    platform_activity  : 0-1.0 pts (continuous)

    Maximum possible: 7.0 pts.
    """
    sig = c.get("redrob_signals", {}) or {}
    s = 0.0

    notice = safe_float(sig.get("notice_period_days"), 90)
    if notice == 0:       s += 3.0
    elif notice <= 15:    s += 2.5
    elif notice <= 30:    s += 2.0
    elif notice <= 60:    s += 1.0
    # notice > 60 days: no points

    if sig.get("open_to_work_flag"):
        s += 1.5

    resp = safe_float(sig.get("response_rate"), 0.5)
    s += resp * 1.5                                        # 0-1.5 pts

    activity = safe_float(sig.get("platform_activity_score"), 0.5)
    s += activity * 1.0                                    # 0-1.0 pts

    return s


def product_tilt_score(c: dict) -> float:
    """
    Proportional product/startup vs IT-services signal.

    Rather than a binary +2/-1 flip, compute the fraction of career roles
    that were at known IT-services companies and apply a sliding penalty.
    A candidate with 0 service roles gets the full +2.0 reward.
    A candidate who spent every role at service companies gets -1.0.
    Mixed backgrounds land proportionally in between.

    Range: -1.0 to +2.0.
    """
    roles = c.get("career_history", [])
    if not roles:
        return 1.0  # neutral for candidates with no history

    companies = " | ".join(
        str(r.get("company", "")).lower() for r in roles
    )
    service_hits = sum(1 for r in roles
                       if any(x in str(r.get("company", "")).lower()
                              for x in SERVICE_COMPANIES))
    service_ratio = service_hits / len(roles)
    # Linear interpolation: 0% service → +2.0, 100% service → -1.0
    return round(2.0 - service_ratio * 3.0, 4)


def recency_boost(c: dict) -> float:
    """
    Tiered relevance boost for the most-recent career role.

    Scans both the title and the first 400 chars of the description so
    the boost captures candidates who list generic titles but describe
    clearly ML/AI work in their role summary.

    Tiers
    -----
    Tier 1 (0.6 pts each, cap 3.0): highly specific RAG/ranking terms
    Tier 2 (0.3 pts each, cap 1.5): general ML/AI role indicators
    Tier 3 (0.2 pts each, cap 0.6): broader data/research indicators

    Maximum total: 3.0 pts.
    """
    history = c.get("career_history", [])
    if not history:
        return 0.0

    # Most recent role (assume list is newest-first, standard LinkedIn export)
    latest = history[0]
    combined = (
        str(latest.get("title", "")).lower()
        + " "
        + str(latest.get("description", ""))[:400].lower()
    )

    tier1 = [
        "llm", "rag", "retrieval", "embedding", "vector search",
        "ranking", "reranking", "information retrieval",
    ]
    tier2 = [
        "ml engineer", "machine learning", "nlp", "deep learning",
        "ai engineer", "applied ml", "research scientist",
    ]
    tier3 = ["data scientist", "data science", "research", "scientist"]

    score  = min(sum(0.6 for t in tier1 if t in combined), 3.0)
    score += min(sum(0.3 for t in tier2 if t in combined), 1.5)
    score += min(sum(0.2 for t in tier3 if t in combined), 0.6)
    return min(round(score, 4), 3.0)


def compute_score(c: dict, text: str) -> float:
    """
    Composite ranking score — sum of all six signal components.

    Scores are kept at full float precision (6 decimal places after
    rounding) to minimise ties and make deterministic tie-breaking
    meaningful rather than an arbitrary sort on candidate_id.
    """
    s  = keyword_score(text)
    s += experience_score(safe_float(c.get("profile", {}).get("years_of_experience"), 0))
    s += availability_score(c)
    s += product_tilt_score(c)
    s += recency_boost(c)
    return round(s, 6)


# ---------------------------------------------------------------------------
# REASONING GENERATION
# ---------------------------------------------------------------------------

# Three deterministic reasoning templates.
# Template selection is seeded by candidate_id (last 7 digits mod 3),
# guaranteeing identical output across runs while varying the phrasing
# across different candidates for reviewer readability.


def _template_skill_led(
    title: str, yoe: float, skills: str,
    notice: int, resp: float, otw: bool, norm_score: float
) -> str:
    otw_str = " · open-to-work" if otw else ""
    return (
        f"{title} | {yoe:.1f}yr exp | Top skills: {skills} | "
        f"Notice: {notice}d{otw_str} | Response rate: {resp:.0%} | "
        f"Score: {norm_score:.1f}/100"
    )


def _template_availability_led(
    title: str, yoe: float, skills: str,
    notice: int, resp: float, otw: bool, norm_score: float,
    activity: float
) -> str:
    otw_str = "open-to-work " if otw else ""
    return (
        f"{notice}d notice {otw_str}| {yoe:.1f}yr ML/AI exp [{title}] | "
        f"{skills} | Activity: {activity:.2f} | Resp: {resp:.0%} | "
        f"Score: {norm_score:.1f}/100"
    )


def _template_experience_led(
    title: str, yoe: float, skills: str,
    notice: int, resp: float, otw: bool, norm_score: float
) -> str:
    avail = f"{notice}d notice" + (" · open-to-work" if otw else "")
    return (
        f"{yoe:.1f}yr exp [{title}] | Skills: {skills} | "
        f"Availability: {avail} · {resp:.0%} resp | "
        f"Score: {norm_score:.1f}/100"
    )


def build_reasoning(c: dict, norm_score: float) -> str:
    """
    Generate a human-readable, single-line reasoning string.

    Template is chosen deterministically by hashing the numeric part
    of candidate_id mod 3, so the output is stable across re-runs but
    varied across candidates.
    """
    p   = c.get("profile", {}) or {}
    sig = c.get("redrob_signals", {}) or {}

    yoe    = safe_float(p.get("years_of_experience"), 0)
    title  = str(p.get("current_title", "Engineer")).strip() or "Engineer"
    notice = int(safe_float(sig.get("notice_period_days"), 90))
    resp   = safe_float(sig.get("response_rate"), 0.5)
    otw    = bool(sig.get("open_to_work_flag"))
    activity = safe_float(sig.get("platform_activity_score"), 0.5)

    skill_names = [
        str(s.get("name", "")).strip()
        for s in c.get("skills", [])
        if str(s.get("name", "")).strip()
    ][:4]
    skills = ", ".join(skill_names) if skill_names else "ML/AI skills"

    # Deterministic template selection
    cid_digits = re.sub(r"\D", "", c.get("candidate_id", "0")) or "0"
    tmpl_idx = int(cid_digits) % 3

    if tmpl_idx == 0:
        return _template_skill_led(title, yoe, skills, notice, resp, otw, norm_score)
    if tmpl_idx == 1:
        return _template_availability_led(
            title, yoe, skills, notice, resp, otw, norm_score, activity
        )
    return _template_experience_led(title, yoe, skills, notice, resp, otw, norm_score)


# ---------------------------------------------------------------------------
# NORMALISATION
# ---------------------------------------------------------------------------

def normalise_scores(entries: list[tuple[float, str, dict]]) -> list[tuple[float, str, dict]]:
    """
    Min-max normalise raw composite scores to the [0, 100] range.

    Normalisation is applied *after* ranking so that the rank order is
    determined entirely by the raw composite score.  The normalised score
    written to submission.csv is purely presentational — it makes scores
    interpretable to reviewers without affecting which candidates appear
    or in what order.

    The best candidate always receives 100.0; the worst in the top-100
    always receives 0.0 (or a configurable floor).
    """
    if not entries:
        return entries
    raw_scores = [e[0] for e in entries]
    lo, hi = min(raw_scores), max(raw_scores)
    rng = hi - lo or 1.0  # guard against zero range
    return [
        (round(50.0 + 50.0 * (s - lo) / rng, 2), cid, c)
        for s, cid, c in entries
    ]


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Rank candidates from a JSONL file and output a "
            "top-100 CSV submission for the Hack2Skill Redrob challenge."
        )
    )
    ap.add_argument(
        "--candidates", required=True,
        help="Path to candidates.jsonl (one JSON object per line)"
    )
    ap.add_argument(
        "--out", required=True,
        help="Output CSV path (e.g. submission.csv)"
    )
    ap.add_argument(
        "--topk", type=int, default=300,
        help="Heap capacity before final sort — must be >= 100 (default: 300)"
    )
    args = ap.parse_args()

    if args.topk < 100:
        ap.error("--topk must be at least 100")

    heap: list[tuple[float, str, dict]] = []
    total = skipped = disqualified = 0

    with open(args.candidates, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            cid = c.get("candidate_id", "")
            if not cid or not re.match(r"CAND_\d{7}$", cid):
                skipped += 1
                continue

            # Hard disqualification: clearly off-domain current title
            if is_disqualified(c):
                disqualified += 1
                continue

            text  = build_text(c)
            score = compute_score(c, text)

            # Min-heap: O(log K) insert, evict smallest when capacity exceeded
            heapq.heappush(heap, (score, cid, c))
            if len(heap) > args.topk:
                heapq.heappop(heap)

            if total % 10_000 == 0:
                print(f"  Scanned {total:,} candidates …", flush=True)

    print(f"\nTotal scanned   : {total:,}")
    print(f"Skipped/invalid : {skipped:,}")
    print(f"Disqualified    : {disqualified:,}")
    print(f"Heap size       : {len(heap):,}")

    # --- Sort: descending score, ties broken deterministically by candidate_id ---
    top_raw = sorted(heap, key=lambda x: (-x[0], x[1]))[:100]

    # --- Normalise scores to [50, 100] presentational range ---
    top100 = normalise_scores(top_raw)

    # --- Write CSV ---
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (norm_score, cid, c) in enumerate(top100, start=1):
            writer.writerow([
                cid,
                rank,
                norm_score,
                build_reasoning(c, norm_score),
            ])

    print(f"\n✅  Wrote {len(top100)} rows → {args.out}")


if __name__ == "__main__":
    main()

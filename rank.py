#!/usr/bin/env python3
"""
redrob-ranker  —  India Runs Data & AI Challenge
Author : Yash Sharma (Yashsh101)
Strategy: Multi-signal keyword + experience + availability + product-tilt scoring
          with deterministic tie-breaking. Streams JSONL line-by-line (O(1) RAM).
"""

import json
import csv
import argparse
import heapq
import re
from typing import Any

# ---------------------------------------------------------------------------
# JD SIGNALS  (Senior AI/ML Engineer – Redrob / India Runs challenge)
# ---------------------------------------------------------------------------
CORE_KEYWORDS = [
    # Retrieval / Vector
    "embedding", "embeddings", "retrieval", "vector", "faiss", "qdrant",
    "weaviate", "milvus", "pinecone", "chroma", "pgvector",
    "elasticsearch", "opensearch", "solr",
    # RAG / Search
    "rag", "retrieval augmented", "semantic search", "dense retrieval",
    "hybrid search", "reranking", "ranking", "information retrieval",
    "bm25", "colbert", "dpr",
    # LLM / GenAI
    "llm", "large language model", "generative ai", "genai",
    "fine-tuning", "fine tuning", "lora", "qlora", "peft", "rlhf",
    "prompt engineering", "instruction tuning", "gpt", "llama", "mistral",
    "gemini", "claude", "openai",
    # NLP / ML Core
    "nlp", "natural language processing", "transformers", "bert", "roberta",
    "sentence transformers", "text classification", "named entity",
    "machine learning", "deep learning", "neural network",
    # MLOps / Infra
    "mlflow", "mlops", "model serving", "triton", "torchserve",
    "kubeflow", "airflow", "feature store", "data pipeline",
    # Frameworks
    "pytorch", "tensorflow", "jax", "huggingface", "langchain",
    "llamaindex", "haystack",
    # Languages
    "python", "sql",
]

# Bonus keywords (niche but highly relevant)
BONUS_KEYWORDS = [
    "candidate ranking", "talent intelligence", "hr tech", "recruitment",
    "applicant tracking", "resume parsing", "job matching",
    "knowledge graph", "graph neural", "multi-modal",
]

# IT-services companies → product-tilt penalty
SERVICE_COMPANIES = [
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "mphasis", "hexaware", "mindtree",
    "l&t infotech", "ltimindtree", "niit technologies", "persistent",
]

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val) if val not in (None, "", "null") else default
    except (ValueError, TypeError):
        return default


def build_text(c: dict) -> str:
    """Concatenate all searchable text fields into one lowercase string."""
    p = c.get("profile", {})
    skills = " ".join(
        str(s.get("name", "")) + " " + str(s.get("category", ""))
        for s in c.get("skills", [])
    )
    career = " ".join(
        str(r.get("title", "")) + " " + str(r.get("description", ""))[:200]
        for r in c.get("career_history", [])
    )
    education = " ".join(
        str(e.get("degree", "")) + " " + str(e.get("field", ""))
        for e in c.get("education", [])
    )
    summary = str(p.get("summary", ""))[:500]
    headline = str(p.get("headline", ""))
    title = str(p.get("current_title", ""))
    return f"{headline} {title} {summary} {skills} {career} {education}".lower()


def count_keywords(text: str) -> tuple[int, int]:
    """Return (core_hits, bonus_hits)."""
    core = sum(1 for k in CORE_KEYWORDS if k in text)
    bonus = sum(1 for k in BONUS_KEYWORDS if k in text)
    return core, bonus


def experience_score(yoe: float) -> float:
    """Sweet spot 5-9 years for a Senior role."""
    if 5 <= yoe <= 9:
        return 6.0
    if 3 <= yoe < 5 or 9 < yoe <= 14:
        return 3.0
    if 2 <= yoe < 3 or 14 < yoe <= 18:
        return 1.0
    return 0.0  # too junior or very senior (likely overqualified)


def availability_score(c: dict) -> float:
    sig = c.get("redrob_signals", {}) or {}
    s = 0.0
    notice = safe_float(sig.get("notice_period_days"), 90)
    if notice == 0:
        s += 3.0
    elif notice <= 15:
        s += 2.5
    elif notice <= 30:
        s += 2.0
    elif notice <= 60:
        s += 1.0
    if sig.get("open_to_work_flag"):
        s += 1.5
    resp = safe_float(sig.get("response_rate"), 0.5)
    s += resp * 1.5  # 0-1.5 points
    activity = safe_float(sig.get("platform_activity_score"), 0.5)
    s += activity * 1.0  # 0-1.0 points
    return s


def product_tilt(c: dict) -> float:
    """Reward product/startup experience over pure IT-services."""
    companies = " ".join(
        str(r.get("company", "")).lower()
        for r in c.get("career_history", [])
    )
    if any(x in companies for x in SERVICE_COMPANIES):
        return -1.0  # mild penalty, not disqualification
    return 2.0


def recency_boost(c: dict) -> float:
    """Tiny boost if most recent role is AI/ML relevant."""
    history = c.get("career_history", [])
    if not history:
        return 0.0
    # assume list ordered newest first (common in LinkedIn-style exports)
    latest_title = str(history[0].get("title", "")).lower()
    ai_titles = ["ml", "ai", "machine learning", "data scientist",
                 "nlp", "research", "llm", "deep learning"]
    return 1.5 if any(t in latest_title for t in ai_titles) else 0.0


def compute_score(c: dict, text: str) -> float:
    core, bonus = count_keywords(text)
    s = core * 1.0          # 1 pt per core keyword hit
    s += bonus * 1.5        # 1.5 pts per bonus keyword
    yoe = safe_float(c.get("profile", {}).get("years_of_experience"), 0)
    s += experience_score(yoe)
    s += availability_score(c)
    s += product_tilt(c)
    s += recency_boost(c)
    return round(s, 4)


def build_reasoning(c: dict, score: float) -> str:
    """Human-readable, concise reasoning string."""
    p = c.get("profile", {}) or {}
    sig = c.get("redrob_signals", {}) or {}
    yoe = safe_float(p.get("years_of_experience"), 0)
    title = str(p.get("current_title", "Engineer")).strip() or "Engineer"
    skills = [
        str(s.get("name", "")).strip()
        for s in c.get("skills", [])
        if str(s.get("name", "")).strip()
    ][:4]
    notice = int(safe_float(sig.get("notice_period_days"), 90))
    resp = safe_float(sig.get("response_rate"), 0)
    otw = "open-to-work" if sig.get("open_to_work_flag") else "not flagged"
    skill_str = ", ".join(skills) if skills else "relevant skills"
    return (
        f"{title} | {yoe:.1f} yrs exp | skills: {skill_str} | "
        f"notice: {notice}d | response_rate: {resp:.2f} | {otw} | score: {score}"
    )


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Rank candidates from a JSONL file and output top-100 CSV."
    )
    ap.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    ap.add_argument("--out", required=True, help="Output CSV path")
    ap.add_argument("--topk", type=int, default=300,
                    help="Heap size before final sort (default 300)")
    args = ap.parse_args()

    heap: list[tuple[float, str, dict]] = []
    total = skipped = 0

    with open(args.candidates, "r", encoding="utf-8") as f:
        for line in f:
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
            if not cid or not re.match(r"CAND_\d{7}", cid):
                skipped += 1
                continue

            text = build_text(c)
            s = compute_score(c, text)

            # Min-heap: evict lowest score when heap exceeds topk
            heapq.heappush(heap, (s, cid, c))
            if len(heap) > args.topk:
                heapq.heappop(heap)

            if total % 10_000 == 0:
                print(f"  Scanned {total:,} candidates ...", flush=True)

    print(f"\nTotal scanned : {total:,}")
    print(f"Skipped/invalid: {skipped:,}")

    # Sort descending by score, break ties by candidate_id (deterministic)
    top100 = sorted(heap, key=lambda x: (-x[0], x[1]))[:100]

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (s, cid, c) in enumerate(top100, start=1):
            writer.writerow([cid, rank, round(s, 4), build_reasoning(c, round(s, 4))])

    print(f"\n✅ Wrote {len(top100)} rows → {args.out}")


if __name__ == "__main__":
    main()

from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from .engine import AI_TERMS, build_reasoning, candidate_id, discover_as_of, full_text, is_disqualified, iter_candidates, normalise_scores, score_candidate

def bm25_scores(candidates):
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        return [0.0] * len(candidates)
    corpus = [full_text(c).split() for c in candidates]
    query = list(dict.fromkeys(" ".join(AI_TERMS).split()))
    return BM25Okapi(corpus).get_scores(query).tolist()

def rank_candidates(candidates, as_of, topk=300):
    eligible = [c for c in candidates if candidate_id(c) and not is_disqualified(c)]
    raw_bm25 = bm25_scores(eligible)
    high = max(raw_bm25) if raw_bm25 else 0.0
    bm25 = [min(10.0, max(0.0, x / high * 10.0)) if high else 0.0 for x in raw_bm25]
    import heapq
    heap = []
    for c, bm in zip(eligible, bm25):
        raw, feat = score_candidate(c, as_of, bm)
        heapq.heappush(heap, (raw, candidate_id(c), c, feat))
        if len(heap) > topk: heapq.heappop(heap)
    return sorted(heap, key=lambda x: (-x[0], x[1]))[:100]

def write_output(entries, out):
    normalized = normalise_scores(entries)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as h:
        writer = csv.writer(h, lineterminator="\n"); writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (_, cid, cand, feat, norm) in enumerate(normalized, 1):
            writer.writerow([cid, rank, f"{norm:.6f}", build_reasoning(cand, feat, rank, norm)])

def run_cli():
    parser = argparse.ArgumentParser(description="Rank Redrob candidates for the India Runs AI Engineer role.")
    parser.add_argument("--candidates", type=Path); parser.add_argument("--out", type=Path); parser.add_argument("--topk", type=int, default=300); parser.add_argument("--as-of-date", type=dt.date.fromisoformat); parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()
    if args.sample:
        sample = Path("official/sample_candidates.json")
        if not sample.exists(): sample = Path("sample_candidates.json")
        candidates = json.loads(sample.read_text(encoding="utf-8")); ranked = rank_candidates(candidates, args.as_of_date or dt.date(2026, 5, 31), max(100, len(candidates)))
        for rank, (_, cid, cand, feat, norm) in enumerate(normalise_scores(ranked), 1): print(f"{rank:03d} {cid} {norm:.6f} {build_reasoning(cand, feat, rank, norm)}")
        return
    if not args.candidates or not args.out: parser.error("--candidates and --out are required unless --sample is used")
    if args.topk < 100: parser.error("--topk must be at least 100")
    if not args.candidates.is_file(): parser.error(f"candidate file not found: {args.candidates}")
    candidates = list(iter_candidates(args.candidates)); as_of = args.as_of_date or discover_as_of(args.candidates); ranked = rank_candidates(candidates, as_of, args.topk)
    if len(ranked) < 100: raise SystemExit(f"Only {len(ranked)} eligible candidates; 100 required")
    write_output(ranked, args.out); print(f"Completed: scanned={len(candidates):,}, output=100, as_of={as_of.isoformat()}")

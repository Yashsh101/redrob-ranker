from __future__ import annotations
import argparse
import csv
import datetime as dt
import heapq
import json
import sys
import time
from pathlib import Path
from .engine import AI_TERMS, build_reasoning, candidate_id, domain_score, fast_domain_score, full_text, normalise_scores, score_candidate, signals, parse_date

PRE_FILTER_K = 10000

def stream_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try: yield json.loads(line)
                except json.JSONDecodeError: continue

def bm25_scores(candidates):
    from rank_bm25 import BM25Okapi
    corpus = [full_text(c).split() for c in candidates]
    query = list(dict.fromkeys(" ".join(AI_TERMS).split()))
    return BM25Okapi(corpus).get_scores(query).tolist()

def rank_candidates(candidates, as_of, limit=None, prefilter_k=PRE_FILTER_K):
    if len(candidates) < 500:
        survivors = list(candidates)
    else:
        heap = []
        for i, c in enumerate(candidates):
            item = (fast_domain_score(c), i, c)
            if len(heap) < prefilter_k: heapq.heappush(heap, item)
            elif item[0] > heap[0][0]: heapq.heapreplace(heap, item)
        survivors = [x[2] for x in heap]
        print(f"[stage1] pre-filter done: {len(survivors)} survivors", file=sys.stderr)
    bm25 = bm25_scores(survivors); high = max(bm25) if bm25 else 0.0
    ranked = []
    for c, value in zip(survivors, bm25):
        if not candidate_id(c): continue
        raw, features = score_candidate(c, as_of, min(10.0, value / high * 10.0) if high else 0.0)
        ranked.append((raw, candidate_id(c), c, features))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return ranked if limit is None else ranked[:limit]

def write_output(entries, out):
    normalized = normalise_scores(entries); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as h:
        writer = csv.writer(h, lineterminator="\n"); writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (_, cid, cand, feat, norm) in enumerate(normalized, 1): writer.writerow([cid, rank, f"{norm:.6f}", build_reasoning(cand, feat, rank, norm)])

def discover_as_of(candidates):
    dates = [parse_date(signals(c).get("last_active_date")) for c in candidates]
    return max((d for d in dates if d), default=dt.date(2026, 5, 31))

def run_cli():
    parser = argparse.ArgumentParser(description="Rank Redrob candidates for the India Runs AI Engineer role.")
    parser.add_argument("--candidates", type=Path); parser.add_argument("--out", type=Path); parser.add_argument("--topk", type=int, default=300); parser.add_argument("--prefilter-k", type=int, default=PRE_FILTER_K); parser.add_argument("--as-of-date", type=dt.date.fromisoformat); parser.add_argument("--sample", action="store_true")
    args = parser.parse_args(); start = time.monotonic()
    if not args.candidates: args.candidates = Path("sample_candidates.json") if args.sample else None
    if not args.candidates or not args.candidates.is_file(): parser.error("candidate file not found; pass --candidates PATH")
    if args.sample:
        candidates = json.loads(args.candidates.read_text(encoding="utf-8")); ranked = rank_candidates(candidates, args.as_of_date or dt.date(2026, 5, 31), prefilter_k=args.prefilter_k); write_output(ranked, args.out or Path("test_sample.csv")); print(f"Sample complete: ranked={len(ranked)}, output={args.out or Path('test_sample.csv')}"); return
    if not args.out: parser.error("--out is required")
    if args.topk < 100 or args.prefilter_k < 100: parser.error("--topk and --prefilter-k must be at least 100")
    candidates = list(stream_jsonl(args.candidates)); ranked = rank_candidates(candidates, args.as_of_date or discover_as_of(candidates), 100, args.prefilter_k)
    if len(ranked) < 100: raise SystemExit(f"Only {len(ranked)} eligible candidates; 100 required")
    write_output(ranked, args.out); print(f"[stage2] scoring done in {time.monotonic()-start:.1f}s", file=sys.stderr); print(f"Completed: scanned={len(candidates):,}, output=100")

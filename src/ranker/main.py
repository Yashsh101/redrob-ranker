from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from .engine import AI_TERMS, build_reasoning, candidate_id, discover_as_of, full_text, normalise_scores, iter_candidates, score_candidate

def bm25_scores(candidates):
    from rank_bm25 import BM25Okapi
    corpus = [full_text(c).split() for c in candidates]
    query = list(dict.fromkeys(" ".join(AI_TERMS).split()))
    return BM25Okapi(corpus).get_scores(query).tolist()

def rank_candidates(candidates, as_of, limit=None):
    scores = bm25_scores(candidates)
    high = max(scores) if scores else 0.0
    bm25 = [min(10.0, max(0.0, x / high * 10.0)) if high else 0.0 for x in scores]
    ranked = []
    for c, bm in zip(candidates, bm25):
        if not candidate_id(c):
            continue
        raw, features = score_candidate(c, as_of, bm)
        ranked.append((raw, candidate_id(c), c, features))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return ranked if limit is None else ranked[:limit]

def write_output(entries, out):
    normalized = normalise_scores(entries)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as h:
        writer = csv.writer(h, lineterminator="\n")
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (_, cid, cand, feat, norm) in enumerate(normalized, 1):
            writer.writerow([cid, rank, f"{norm:.6f}", build_reasoning(cand, feat, rank, norm)])

def run_cli():
    parser = argparse.ArgumentParser(description="Rank Redrob candidates for the India Runs AI Engineer role.")
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--topk", type=int, default=300)
    parser.add_argument("--as-of-date", type=dt.date.fromisoformat)
    parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()
    if not args.candidates:
        args.candidates = Path("sample_candidates.json") if args.sample else None
    if args.sample:
        if not args.candidates or not args.candidates.is_file():
            parser.error("sample_candidates.json not found; pass --candidates PATH")
        candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
        ranked = rank_candidates(candidates, args.as_of_date or dt.date(2026, 5, 31))
        write_output(ranked, args.out or Path("test_sample.csv"))
        print(f"Sample complete: ranked={len(ranked)}, output={args.out or Path('test_sample.csv')}")
        return
    if not args.candidates or not args.out:
        parser.error("--candidates and --out are required unless --sample is used")
    if args.topk < 100: parser.error("--topk must be at least 100")
    if not args.candidates.is_file(): parser.error(f"candidate file not found: {args.candidates}")
    candidates = list(iter_candidates(args.candidates))
    ranked = rank_candidates(candidates, args.as_of_date or discover_as_of(args.candidates), 100)
    if len(ranked) < 100: raise SystemExit(f"Only {len(ranked)} eligible candidates; 100 required")
    write_output(ranked, args.out)
    print(f"Completed: scanned={len(candidates):,}, output=100")

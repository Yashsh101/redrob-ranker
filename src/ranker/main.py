from __future__ import annotations

import argparse
import csv
import datetime as dt
import heapq
import json
import re
from pathlib import Path
from typing import Any, Iterable

from .engine import (
    is_disqualified,
    parse_date,
    score_candidate,
)


def normalise_scores(entries: list[tuple[float, str, dict[str, Any], dict[str, Any]]]) -> list[tuple[float, str, dict[str, Any], dict[str, Any], float]]:
    if not entries:
        return []
    scores = [entry[0] for entry in entries]
    low, high = min(scores), max(scores)
    span = high - low or 1.0
    return [(raw, cid, cand, feat, round((raw - low) / span, 6)) for raw, cid, cand, feat in entries]


def build_reasoning(candidate: dict[str, Any], features: dict[str, Any], rank: int, normalized_score: float) -> str:
    evidence = ", ".join(features["evidence"][:3]) or "adjacent technical evidence"
    matched = ", ".join(features["matched_skills"][:3]) or "no named core skill"
    signals = f"{features['response']:.0%} recruiter response, {features['notice_days']}d notice"
    concern = features["concerns"][0]
    title = features["title"]
    years = features["years"]
    
    if rank <= 10:
        lead = "Strong match"
    elif rank <= 50:
        lead = "Relevant match"
    else:
        lead = "Lower-confidence match"
        
    variant = int(re.sub(r"\D", "", str(candidate.get("candidate_id", "0"))) or "0") % 4
    if variant == 0:
        return f"{lead}: {title} with {years:.1f} years; profile evidence covers {evidence} and named skills include {matched}. Signals: {signals}; concern: {concern}."
    if variant == 1:
        return f"{lead} for the Senior AI Engineer role because the career history shows {evidence} and the profile lists {matched}; {years:.1f} years of experience. Availability signals: {signals}; watchout: {concern}."
    if variant == 2:
        return f"{lead}: current title is {title}, with {years:.1f} years and evidence of {evidence}; relevant listed skills: {matched}. The main qualification concern is {concern}; recruiter response is {features['response']:.0%}."
    return f"{lead} based on {evidence} in the career record rather than keyword count alone; current title {title}, {years:.1f} years, skills {matched}. Behaviour: {signals}; caveat: {concern}."


def iter_candidates(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def discover_as_of(path: Path) -> dt.date:
    latest: dt.date | None = None
    for candidate in iter_candidates(path):
        value = parse_date((candidate.get("redrob_signals", {}) or {}).get("last_active_date"))
        if value and (latest is None or value > latest):
            latest = value
    return latest or dt.date(2026, 5, 31)


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Rank Redrob candidates for the India Runs Track 1 Senior AI Engineer JD.")
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--topk", type=int, default=300)
    parser.add_argument("--as-of-date", type=dt.date.fromisoformat, help="Optional ISO date; default is max last_active_date in the dataset")
    parser.add_argument("--diagnostics", type=Path, help="Optional JSON diagnostics path")
    args = parser.parse_args()

    if args.topk < 100:
        parser.error("--topk must be at least 100")
    if not args.candidates.is_file():
        parser.error(f"candidate file not found: {args.candidates}")

    as_of = args.as_of_date or discover_as_of(args.candidates)
    heap: list[tuple[float, str, dict[str, Any], dict[str, Any]]] = []
    scanned = skipped = disqualified = 0

    print(f"Starting ranker with as_of={as_of.isoformat()}...", flush=True)

    for candidate in iter_candidates(args.candidates):
        scanned += 1
        cid = str(candidate.get("candidate_id", ""))
        if not re.fullmatch(r"CAND_\d{7}", cid):
            skipped += 1
            continue
        if is_disqualified(candidate):
            disqualified += 1
            continue
        
        raw_score, features = score_candidate(candidate, as_of)
        heapq.heappush(heap, (raw_score, cid, candidate, features))
        if len(heap) > args.topk:
            heapq.heappop(heap)
        
        if scanned % 10000 == 0:
            print(f"Scanned {scanned:,} candidates...", flush=True)

    # Sort by score descending, then candidate_id ascending for deterministic ties
    ranked = sorted(heap, key=lambda item: (-item[0], item[1]))[:100]
    normalized = normalise_scores(ranked)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (raw, cid, cand, feat, norm) in enumerate(normalized, start=1):
            writer.writerow([cid, rank, f"{norm:.6f}", build_reasoning(cand, feat, rank, norm)])

    if args.diagnostics:
        diagnostics = {
            "as_of_date": as_of.isoformat(),
            "scanned": scanned,
            "skipped": skipped,
            "disqualified": disqualified,
            "heap_size": len(heap),
            "output_rows": len(normalized),
            "top100": [
                {"candidate_id": cid, "rank": rank, "raw_score": round(raw, 8), "features": feat}
                for rank, (raw, cid, cand, feat, norm) in enumerate(normalized, start=1)
            ],
        }
        args.diagnostics.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")

    print(f"Completed. Scanned: {scanned:,}; skipped: {skipped:,}; disqualified: {disqualified:,}; wrote: {len(normalized)} rows.")

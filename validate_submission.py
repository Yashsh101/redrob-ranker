#!/usr/bin/env python3
"""Validate the ranked CSV contract required by the Track 1 submission."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REQUIRED_COLUMNS = ["candidate_id", "rank", "score", "reasoning"]
CANDIDATE_ID_RE = re.compile(r"^CAND_\d{7}$")


def validate(path: Path, *, require_normalized_scores: bool = False) -> list[str]:
    errors: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REQUIRED_COLUMNS:
            return [
                f"columns must be exactly {REQUIRED_COLUMNS}; got {reader.fieldnames}"
            ]
        rows = list(reader)

    if len(rows) != 100:
        errors.append(f"expected exactly 100 data rows; got {len(rows)}")

    ids: list[str] = []
    ranks: list[int] = []
    scores: list[float] = []
    for line_number, row in enumerate(rows, start=2):
        candidate_id = row["candidate_id"]
        if not CANDIDATE_ID_RE.fullmatch(candidate_id):
            errors.append(f"line {line_number}: invalid candidate_id {candidate_id!r}")
        ids.append(candidate_id)

        try:
            rank = int(row["rank"])
        except ValueError:
            errors.append(f"line {line_number}: rank is not an integer")
            continue
        ranks.append(rank)

        try:
            score = float(row["score"])
        except ValueError:
            errors.append(f"line {line_number}: score is not numeric")
            continue
        scores.append(score)
        if not row["reasoning"].strip():
            errors.append(f"line {line_number}: reasoning is empty")

    if len(ids) == len(set(ids)) and len(ids) == 100:
        pass
    elif len(ids) != len(set(ids)):
        errors.append("candidate_id values must be unique")

    if ranks and ranks != list(range(1, len(rows) + 1)):
        errors.append("rank values must be the ordered sequence 1..100")

    if require_normalized_scores and scores and any(score < 50.0 or score > 100.0 for score in scores):
        errors.append("normalized scores must be within the inclusive range 50.0..100.0")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument(
        "--require-normalized",
        action="store_true",
        help="require the ranker's normalized 50.0..100.0 score range",
    )
    args = parser.parse_args()
    if not args.submission.is_file():
        print(f"submission file not found: {args.submission}", file=sys.stderr)
        return 2
    errors = validate(args.submission, require_normalized_scores=args.require_normalized)
    if errors:
        print("submission validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"submission validation passed: {args.submission}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

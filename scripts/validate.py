#!/usr/bin/env python3
"""Validate an India Runs Track 1 submission against the organizer CSV rules."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]
CANDIDATE_ID_PATTERN = re.compile(r"^CAND_[0-9]{7}$")
EXPECTED_DATA_ROWS = 100


def validate_submission(
    csv_path: Path,
    *,
    require_normalized: bool = False,
    candidates_path: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if csv_path.suffix.lower() != ".csv":
        errors.append("filename must use a .csv extension")
    if not csv_path.stem:
        errors.append("filename must contain a registered participant ID")
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                return ["file is empty; row 1 must be the header"]
            if header != REQUIRED_HEADER:
                errors.append(f"header must be exactly {REQUIRED_HEADER}; got {header}")
            rows = [row for row in reader if any(cell.strip() for cell in row)]
    except UnicodeDecodeError:
        return ["file must be UTF-8 encoded"]
    except OSError as exc:
        return [f"cannot read file: {exc}"]

    if len(rows) != EXPECTED_DATA_ROWS:
        errors.append(f"expected exactly {EXPECTED_DATA_ROWS} data rows; got {len(rows)}")
    seen_ids: set[str] = set()
    seen_ranks: set[int] = set()
    by_rank: list[tuple[int, float, str]] = []
    for index, cells in enumerate(rows, start=2):
        if len(cells) != len(REQUIRED_HEADER):
            errors.append(f"row {index}: expected 4 columns; got {len(cells)}")
            continue
        row = dict(zip(REQUIRED_HEADER, cells))
        candidate_id = row["candidate_id"].strip()
        if not CANDIDATE_ID_PATTERN.fullmatch(candidate_id):
            errors.append(f"row {index}: invalid candidate_id {candidate_id!r}")
        elif candidate_id in seen_ids:
            errors.append(f"row {index}: duplicate candidate_id {candidate_id}")
        else:
            seen_ids.add(candidate_id)
        try:
            rank = int(row["rank"])
            if str(rank) != row["rank"].strip() or not 1 <= rank <= 100:
                raise ValueError
            if rank in seen_ranks:
                errors.append(f"row {index}: duplicate rank {rank}")
            seen_ranks.add(rank)
        except ValueError:
            errors.append(f"row {index}: rank must be an integer from 1 to 100")
            continue
        try:
            score = float(row["score"])
        except ValueError:
            errors.append(f"row {index}: score must be numeric")
            continue
        if require_normalized and not 0.0 <= score <= 1.0:
            errors.append(f"row {index}: normalized score must be in 0.0..1.0")
        if not row["reasoning"].strip():
            errors.append(f"row {index}: reasoning must not be empty")
        by_rank.append((rank, score, candidate_id))

    if seen_ranks != set(range(1, 101)):
        errors.append(f"ranks must contain each integer 1..100 exactly once; got {sorted(seen_ranks)[:5]}...")
    if candidates_path is not None:
        if not candidates_path.is_file():
            errors.append(f"candidate file not found: {candidates_path}")
        else:
            candidate_ids: set[str] = set()
            with candidates_path.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        try:
                            import json
                            candidate_ids.add(str(json.loads(line).get("candidate_id", "")))
                        except json.JSONDecodeError:
                            errors.append("candidate file contains invalid JSON")
                            break
            missing = sorted(seen_ids - candidate_ids)
            if missing:
                errors.append(f"submitted candidate IDs not found in candidate file: {missing[:5]}")
    by_rank.sort()
    for previous, current in zip(by_rank, by_rank[1:]):
        if previous[1] < current[1]:
            errors.append(f"score must be non-increasing: rank {previous[0]} < rank {current[0]}")
        if previous[1] == current[1] and previous[2] > current[2]:
            errors.append(f"equal-score tie must use candidate_id ascending: {previous[2]} > {current[2]}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument("--require-normalized", action="store_true", help="require the ranker's 0.0..1.0 score range")
    parser.add_argument("--candidates", type=Path, help="optional released JSONL file for candidate-ID existence checks")
    args = parser.parse_args()
    if not args.submission.is_file():
        print(f"submission not found: {args.submission}", file=sys.stderr)
        return 2
    errors = validate_submission(
        args.submission,
        require_normalized=args.require_normalized,
        candidates_path=args.candidates,
    )
    if errors:
        print(f"validation failed ({len(errors)} issue(s))")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Submission is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

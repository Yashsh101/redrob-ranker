#!/usr/bin/env python3
"""Evaluate a ranked CSV when organizer ground-truth labels are available.

Accepted label formats:
- CSV with candidate_id and relevance (or tier) columns
- JSONL objects with candidate_id and relevance (or tier)

For multi-query labels, include query_id in both the prediction and label files;
the current India Runs task publishes one released job description, so the
single-query form is the default.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


def read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() in {".jsonl", ".json"}:
        rows = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def relevance(row: dict[str, Any]) -> float:
    value = row.get("relevance", row.get("tier", row.get("label")))
    if value is None:
        raise ValueError("labels require a relevance, tier, or label column")
    return float(value)


def dcg(values: list[float], k: int) -> float:
    return sum(value / math.log2(index + 2) for index, value in enumerate(values[:k]))


def ndcg(ranked: list[float], labels: list[float], k: int) -> float:
    ideal = dcg(sorted(labels, reverse=True), k)
    return dcg(ranked, k) / ideal if ideal else 0.0


def average_precision(ranked: list[float], total_relevant: int | None = None) -> float:
    relevant = 0
    precision_sum = 0.0
    denominator = total_relevant if total_relevant is not None else sum(value > 0 for value in ranked)
    if denominator == 0:
        return 0.0
    for index, value in enumerate(ranked, start=1):
        if value > 0:
            relevant += 1
            precision_sum += relevant / index
    return precision_sum / denominator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    args = parser.parse_args()
    predictions = read_rows(args.submission)
    label_rows = read_rows(args.labels)
    labels = {str(row["candidate_id"]): relevance(row) for row in label_rows}
    ranked_ids = [str(row["candidate_id"]) for row in sorted(predictions, key=lambda row: int(row["rank"]))]
    ranked_relevance = [labels.get(cid, 0.0) for cid in ranked_ids]
    all_relevance = list(labels.values())
    metrics = {
        "ndcg_at_10": ndcg(ranked_relevance, all_relevance, 10),
        "ndcg_at_50": ndcg(ranked_relevance, all_relevance, 50),
        "map": average_precision(ranked_relevance, sum(value > 0 for value in all_relevance)),
        "p_at_10": sum(value >= 3 for value in ranked_relevance[:10]) / 10.0,
    }
    metrics["composite"] = (
        0.50 * metrics["ndcg_at_10"]
        + 0.30 * metrics["ndcg_at_50"]
        + 0.15 * metrics["map"]
        + 0.05 * metrics["p_at_10"]
    )
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

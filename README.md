# RedRob India Runs Ranker 2026

A professional candidate ranking system built for the India Runs Track 1 challenge. This system identifies the strongest candidates for a **Senior AI Engineer** role by analyzing career history, technical fit, and behavioral signals from the Redrob dataset.

## Project Structure

The repository follows a modular engineering structure:

```text
redrob-ranker/
├── src/ranker/         # Core application logic
│   ├── engine.py       # Scoring algorithms and JD alignment
│   └── main.py         # CLI and streaming orchestration
├── scripts/            # Utility tools (validate, evaluate)
├── tests/              # Comprehensive unit tests
├── docs/               # Reports, architecture, and templates
├── data/output/        # Generated submission and diagnostics
├── rank.py             # Main entry point (root)
├── pyproject.toml      # Project configuration
└── README.md           # Documentation
```

## Features

- **JD-Specific Scoring**: Explicit signals for retrieval/ranking, production ML, and evaluation literacy.
- **Trap Resistance**: Filters for off-domain titles, career gaps, and suspicious skill claims.
- **Behavioral Analysis**: Weights platform activity, recruiter response rates, and availability.
- **Explainable AI**: Generates unique, factual, and rank-consistent reasoning for every candidate.
- **Resource Efficient**: Processes 100k candidates in ~3.5 minutes using < 25MB RAM (CPU-only).

## Getting Started

### Prerequisites
- Python 3.10+
- `pytest` (for development/testing)

### Installation
```bash
git clone https://github.com/Yashsh101/redrob-ranker.git
cd redrob-ranker
pip install -e ".[dev]"
```

### Usage

**Run the Ranker:**
```bash
python rank.py --candidates /path/to/candidates.jsonl --out data/output/submission.csv --diagnostics data/output/diagnostics.json
```

**Validate a Submission:**
```bash
python scripts/validate.py data/output/submission.csv --require-normalized --candidates /path/to/candidates.jsonl
```

**Run Tests:**
```bash
python -m pytest
```

## Official Requirements Compliance

- **Format**: Exactly 100 rows, unique IDs, ranks 1–100, non-increasing scores.
- **Compute**: CPU-only, offline, < 300s wall-clock, < 16GB RAM.
- **Metrics**: Ready for NDCG@10, NDCG@50, MAP, and P@10 evaluation.

## License
MIT

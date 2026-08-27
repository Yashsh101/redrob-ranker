# RedRob India Runs Ranker 2026 — Senior AI Engineer

[![Engineering Readiness](https://img.shields.io/badge/Engineering%20Readiness-9%2F10-success)](docs/reports/INDIA_RUNS_UPGRADE_REPORT.md)
[![Compliance](https://img.shields.io/badge/Compliance-Official%20Validator-blue)](scripts/validate.py)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

An evidence-backed, production-grade candidate discovery and ranking system engineered for the **India Runs 2026 Track 1 Challenge**. This system identifies top-tier talent for a Founding Team **Senior AI Engineer** role by analyzing 100,000 profiles across technical fit, career history, and behavioral reliability.

## 🚀 Key Engineering Highlights

- **JD-Specific Scoring Engine**: Beyond keyword matching, the system uses semantic signal groups for Retrieval/Ranking, Production ML, and Evaluation literacy.
- **Trap-Resistant Architecture**: Implements proactive guards against off-domain title traps, "Expert" skill anomalies, and career history inconsistencies.
- **Behavioral Intelligence**: Integrates platform engagement (response rates, activity recency) as a dynamic modifier to technical fit.
- **High-Performance Streaming**: Processes the entire 100k candidate dataset in **~204 seconds** using **< 25MB RAM** (CPU-only, standard library).
- **Explainable AI (XAI)**: Generates 100% unique, factual, and rank-consistent reasoning for every shortlisted candidate.

## 📁 Project Structure

```text
redrob-ranker/
├── src/ranker/         # Core Engine: Scoring logic and JD alignment
├── scripts/            # Tooling: Official validation and evaluation scripts
├── tests/              # Reliability: Comprehensive unit and metric tests
├── docs/               # Intelligence: Architecture, methodology, and audit reports
├── data/output/        # Artifacts: Final submission and diagnostics
├── rank.py             # Entry Point: Standardized root execution script
├── pyproject.toml      # Configuration: Modern Python packaging
└── README.md           # Documentation
```

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+
- `pytest` (for development)

### Installation
```bash
git clone https://github.com/Yashsh101/redrob-ranker.git
cd redrob-ranker
pip install -e ".[dev]"
```

### Usage

**1. Run the Ranker**
```bash
python rank.py --candidates /path/to/candidates.jsonl --out data/output/submission.csv
```

**2. Validate Submission**
```bash
python scripts/validate.py data/output/submission.csv --require-normalized
```

**3. Run Test Suite**
```bash
python -m pytest
```

## 📊 Ranking Methodology
The system uses a multi-dimensional weighted model:
- **Technical Fit (60%)**: Career-weighted evidence of RAG, Vector Search, and MLOps.
- **Experience (20%)**: Non-linear curve peaking at the ideal 6–8 year band.
- **Behavioral (20%) Modifier**: Activity recency, recruiter response rate, and profile completeness.

Detailed methodology is available in the [Ranking Methodology Report](docs/reports/RANKING_METHODOLOGY.md).

## ⚖️ Official Compliance

| Requirement | Status | Verification |
| :--- | :---: | :--- |
| **Format** | ✅ | Exactly 100 rows, unique IDs, ranks 1–100 |
| **Compute** | ✅ | CPU-only, Offline, No network calls |
| **Time** | ✅ | 204.6s (Limit: 300s) |
| **Memory** | ✅ | 21.45MB (Limit: 16GB) |
| **Validator** | ✅ | Passes official organizer check |

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
Built with 💡 for the **India Runs 2026** challenge by [Yash Sharma](https://yashsharma01.vercel.app/).

# 🏆 RedRob Ranker — India Runs Data & AI Challenge

> **Track 1: Data & AI Challenge** — Smart AI Candidate Ranking System
> Built by [Yash Sharma](https://yashsharma01.vercel.app/) · [@Yashsh101](https://github.com/Yashsh101)

---

## 🎯 Problem Statement

Rank ~100,000 candidate profiles for the role of **Senior AI/ML Engineer at Redrob** and output a top-100 shortlist with scores and reasoning — going beyond keyword filters to understand real fit, seniority, and availability.

---

## 🧠 Approach

### Multi-Signal Scoring Architecture

A fast, single-pass streaming ranker that computes a composite scalar score per candidate across **5 independent signal dimensions**:

| Signal | Weight | Rationale |
|---|---|---|  
| **Keyword relevance** | 1.0–1.5 pts/hit | 25 core + 9 bonus terms from JD (RAG, embeddings, LLM, NLP etc.) |
| **Experience fit** | 0–6 pts | Sweet spot 5–9 yrs for Senior role; penalty for too-junior/over-senior |
| **Availability** | 0–8 pts | Notice period, open-to-work flag, response rate, platform activity |
| **Product tilt** | ±1–2 pts | Reward product/startup experience; mild penalty for pure IT-services |
| **Recency boost** | 0–1.5 pts | Boost if most recent role is AI/ML titled |

### Design Decisions

- **Streaming JSONL** — reads line-by-line, O(1) RAM regardless of dataset size
- **Min-heap of size 300** — keeps only top-300 candidates in memory at any time
- **Deterministic tie-breaking** — sort by `(-score, candidate_id)` for reproducibility
- **Regex validation** — skips malformed `candidate_id` values (must match `CAND_\d{7}`)
- **No heavy dependencies** — pure Python stdlib + numpy; runs on any machine in seconds

---

## 🚀 Quick Start

```bash
# 1. Clone & install
git clone https://github.com/Yashsh101/redrob-ranker.git
cd redrob-ranker
pip install -r requirements.txt

# 2. Run ranker
python rank.py \
  --candidates path/to/candidates.jsonl \
  --out submission.csv

# 3. Validate
python validate_submission.py submission.csv
```

---

## 📁 Repository Structure

```
redrob-ranker/
├── rank.py                  # Main ranking engine
├── fix_tiebreak.py          # Utility: re-apply tie-break to existing CSV
├── submission.csv           # Final validated submission (top-100)
├── requirements.txt         # Minimal dependencies
├── validate_submission.py   # Official challenge validator
├── .gitignore
├── .github/
│   └── workflows/
│       └── rank.yml         # GitHub Actions CI — auto-ranks on push
└── README.md
```

---

## 🔄 Automated Pipeline (GitHub Actions)

Every push to `main` that modifies `rank.py` or `candidates.jsonl` automatically:
1. Runs the ranker
2. Validates the submission
3. Uploads `submission.csv` as a downloadable artifact

You can also trigger it manually via **Actions → Auto-Rank Candidates → Run workflow**.

---

## 📊 Scoring Formula

```
score = (core_keyword_hits × 1.0)
      + (bonus_keyword_hits × 1.5)
      + experience_score(yoe)        # 0 | 1 | 3 | 6
      + availability_score(signals)  # notice + open_to_work + response_rate + activity
      + product_tilt(career)         # +2.0 or -1.0
      + recency_boost(latest_role)   # 0 or +1.5
```

---

## 🏅 Submission Format

```
candidate_id,rank,score,reasoning
CAND_0000001,1,42.5,"Senior ML Engineer | 7.0 yrs exp | skills: RAG, embeddings, PyTorch, LLM | notice: 0d | response_rate: 0.92 | open-to-work | score: 42.5"
...
```

100 rows · unique ranks 1–100 · `candidate_id` matches `CAND_\d{7}`

---

## 🛠 Tech Stack

`Python 3.11` · `stdlib only (json, csv, heapq, re, argparse)` · `GitHub Actions`

---

*Built for the India Runs Data & AI Hackathon 2026 — [hack2skill.com](https://hack2skill.com)*

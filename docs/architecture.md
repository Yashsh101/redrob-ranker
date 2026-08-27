# RedRob Ranker Architecture

## Overview
The RedRob Ranker is a modular, CPU-only, offline ranking system designed for the India Runs 2026 challenge. It scores candidates against a specific Senior AI Engineer job description using a combination of technical fit, career history, and behavioral signals.

## Directory Structure
- `src/ranker/`: Core application logic.
  - `engine.py`: The scoring engine containing constants and fit algorithms.
  - `main.py`: CLI orchestration and streaming I/O.
- `scripts/`: Utility scripts for validation and evaluation.
- `tests/`: Comprehensive test suite for the engine and metrics.
- `docs/`: Documentation, reports, and templates.
- `data/output/`: Generated submission files and diagnostics.

## Scoring Engine
The engine uses a multi-factor scoring model:
1. **Technical Fit**: Keyword matching against JD-specific groups (Retrieval, ML/LLM, Production, Evaluation).
2. **Experience Fit**: A non-linear scoring curve peaking at the ideal 6–8 year band.
3. **Behavioral Signals**: A weighted modifier based on platform activity, response rates, and profile completeness.
4. **Contextual Signals**: Penalties for off-domain titles, career gaps, and suspicious expert-skill claims.

## Performance & Reproducibility
- **Offline**: No network calls are made during the ranking process.
- **Deterministic**: Ties are handled by candidate ID to ensure consistent results.
- **Efficient**: Uses a streaming JSONL reader and a min-heap to process 100,000 candidates in under 4 minutes with < 25MB RAM.

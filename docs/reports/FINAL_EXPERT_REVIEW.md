# Final Expert Review & Rating Report

**Repository:** `Yashsh101/redrob-ranker`
**Audited commit:** `c39b70d`
**Audit scope:** source structure, tests, committed submission, validator, dependency declarations, and benchmark evidence.

## Executive verdict

The repository is a strong, deterministic challenge submission with a clear `src/` layout, a bounded pre-filter, one BM25 build on survivors, normalized output, and an official-format validator. The committed submission is structurally valid and the local test suite passes. It is **not** accurate to call the project a 10/10 production system: the official 100k benchmark cannot be reproduced without the organizer dataset, the ranking model still has a documented off-domain top-10 limitation, and the repository is a CLI package rather than a deployed web service.

## Evidence checked

| Check | Result |
|---|---|
| Unit tests | **9/9 passed** |
| Committed submission | **Validator passed** with normalized scores |
| Submission rows | **100** |
| Unique candidate IDs | **100** |
| Unique reasoning strings | **100** |
| Rank sequence | **1–100** |
| Score range/order | **0.0–1.0; non-increasing** |
| Dependency check | **No broken requirements** |
| Official 100k input | **Not present in audit environment** |
| Fresh 100k runtime/RSS | **Not re-measured in this audit** |

## Expert rating summary

| Metric | Rating | Rationale |
|---|---:|---|
| Official format compliance | **9.5/10** | Committed CSV passes the repository validator and has the required shape. |
| Test coverage | **8.5/10** | 9 tests pass across engine behavior and ranking metrics; more end-to-end fixtures would help. |
| Determinism | **9/10** | Stable score ordering and candidate-ID tie-breaking are implemented. |
| Ranking logic | **8.3/10** | Multi-signal scoring, BM25, career evidence, availability, and domain gating are useful; calibration remains open. |
| Domain gating | **8/10** | Strong off-domain penalties exist, but off-domain titles can still appear in top-10. |
| Explainability | **8.5/10** | Reasoning is candidate-specific and includes score/evidence fields; factuality depends on input quality. |
| Performance evidence | **8.5/10** | The README records a 71.8s / 1.85GB local benchmark, but the organizer dataset was unavailable for fresh rerun here. |
| Code architecture | **8.3/10** | Good separation between engine, CLI, scripts, tests, and data artifacts. |
| Documentation | **8/10** | Architecture and methodology are documented; benchmark caveats are now explicit. |
| Engineering readiness | **8/10** | CI now covers lint, tests, package build, and manual artifact publication. |
| Deployment readiness | **2/10** | The canonical repository is intentionally ranker-only and has no API/frontend or Vercel configuration. |
| Overall | **8.2/10** | Strong challenge submission; not yet a production web product. |

## Dependencies and runtime

This project is **not standard-library-only**. Runtime dependencies declared in `requirements.txt` are:

- `rank_bm25`
- `numpy`
- `python-dateutil`

Development dependencies are declared in `requirements-dev.txt` and include `pytest`. The ranking workflow is designed to run CPU-only and offline after dependencies are installed; no neural inference or network calls are required during ranking.

## Benchmark interpretation

The README reports a prior local benchmark of **71.8 seconds wall time** and **1.85GB peak RSS** on the official 100k candidate dataset. These are local machine measurements, not organizer scores. Because that dataset is not included in the repository and was unavailable during this audit, this report does **not** present those values as a fresh reproduction or guarantee identical results on another machine.

## Strengths

- Clean `src/ranker/` package layout.
- Deterministic ranking and normalized output.
- Single BM25 construction after structured pre-filtering.
- Official-format validation script.
- Candidate-specific reasoning output.
- No raw candidate dataset committed to Git.
- CI checks syntax, lint errors, tests, validator compliance, and package build.

## Remaining risks

1. **Calibration:** off-domain titles remain possible in the top-10; labelled relevance data would improve threshold tuning.
2. **Benchmark reproducibility:** publish the exact hardware, Python version, dependency versions, and a reproducible benchmark command alongside organizer-approved data access.
3. **Test depth:** add a small anonymized end-to-end fixture covering malformed records, ties, disqualified titles, and pre-filter boundary behavior.
4. **Product surface:** keep this challenge repository ranker-only; use a separate API/frontend repository for any live demo.

## Conclusion

`redrob-ranker` is **submission-ready and technically credible**, with honest limitations. The evidence supports an overall **8.2/10**, not a blanket 10/10. The next highest-value improvement is offline calibration against labelled relevance data, followed by stronger end-to-end fixtures.

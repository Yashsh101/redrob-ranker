# Final Expert Review & Rating Report

**Repository:** `Yashsh101/redrob-ranker`  
**Audit scope:** challenge-relevant ranking quality, official output compliance, tests, determinism, performance evidence, code, documentation, and domain-gate regression behavior.

## Executive verdict

The repository is a strong, deterministic challenge submission with a clear `src/` layout, bounded pre-filtering, one BM25 build on survivors, normalized output, and an official-format validator. The committed submission is structurally valid and the local test suite passes.

**Deployment is intentionally excluded from the score.** The challenge scope is the ranking system and its submission output; it did not require a public web deployment. The repository is correctly kept ranker-only.

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
| Public deployment | **Not a challenge scoring criterion** |
| Off-domain top-10 regression | **PASS** on synthetic regression for configured title exclusions |

## India Runs rules alignment

The official Track 1 checklist asks for three core deliverables: **complete code**, a clear **README/blueprint**, and a **ranked output file**. The repository contains all three. Public deployment is not listed as a Track 1 deliverable.

The implementation also follows the repository's recorded submission constraints: exactly 100 output rows, required CSV columns, deterministic ordering, CPU-only execution, no network calls during ranking, and normalized scores. The official terms additionally require original work, no third-party rights violations, no false or misleading claims, and no malware; this audit found no dependency or source change that violates those requirements.

## Challenge-focused rating summary

| Metric | Rating | Rationale |
|---|---:|---|
| Official format compliance | **9.5/10** | Committed CSV passes the repository validator and has the required shape. |
| Test coverage | **8.5/10** | 9 tests pass across engine behavior and ranking metrics; more end-to-end fixtures would help. |
| Determinism | **9/10** | Stable score ordering and candidate-ID tie-breaking are implemented. |
| Ranking logic | **8.3/10** | Multi-signal scoring, BM25, career evidence, availability, and domain gating are useful; calibration remains open. |
| Domain gating | **9/10** | Configured off-domain titles are now hard-excluded before pre-filtering and BM25; broader labelled calibration is still possible. |
| Explainability | **8.5/10** | Reasoning is candidate-specific and includes score/evidence fields; factuality depends on input quality. |
| Performance evidence | **8.5/10** | README records a 71.8s / 1.85GB local benchmark; the organizer dataset was unavailable for fresh rerun here. |
| Code architecture | **8.3/10** | Good separation between engine, CLI, scripts, tests, and data artifacts. |
| Documentation | **8/10** | Architecture and methodology are documented; benchmark caveats are explicit. |
| Engineering readiness | **8/10** | CI covers lint, tests, package build, and manual artifact publication. |
| **Overall challenge score** | **8.6/10** | Average of the 10 challenge-relevant criteria above, rounded from 8.56 after the domain-gate fix. |

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
- Repository scope remains aligned with a ranker-only challenge submission.
- Configured off-domain current titles are removed before candidate retrieval and scoring.

## Remaining risks

1. **Calibration:** the hard gate now blocks configured off-domain titles; labelled relevance data is still needed to tune borderline titles such as generic software/backend roles.
2. **Benchmark reproducibility:** publish exact hardware, Python version, dependency versions, and a reproducible benchmark command alongside organizer-approved data access.
3. **Test depth:** add a small anonymized end-to-end fixture covering malformed records, ties, disqualified titles, and pre-filter boundary behavior.

## Conclusion

`redrob-ranker` is **submission-ready and technically credible**. Based on challenge-relevant criteria, the final expert score is **8.6/10** after fixing the domain-gate pipeline defect. The next highest-value improvement is offline calibration against labelled relevance data, followed by stronger end-to-end fixtures. Public deployment is optional and intentionally not part of this score.

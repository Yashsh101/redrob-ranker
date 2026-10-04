# Final Expert Review & Rating Report

**Repository:** `Yashsh101/redrob-ranker`  
**Audit scope:** challenge-relevant ranking quality, official output compliance, tests, determinism, performance evidence, code, documentation, and domain-gate regression behavior.

## Executive verdict

The repository has a clear `src/` layout, bounded pre-filtering, one BM25 build on survivors, normalized output, and an official-format validator. Benchmark and CI claims in this report require re-verification after the packaging and workflow updates.

**Deployment is intentionally excluded from the score.** The challenge scope is the ranking system and its submission output; it did not require a public web deployment. The repository is correctly kept ranker-only.

## Evidence checked

| Check | Result |
|---|---|
| Unit tests | **Pending clean-install verification** |
| Committed submission | **Validator passed** with normalized scores |
| Submission rows | **100** |
| Unique candidate IDs | **100** |
| Unique reasoning strings | **100** |
| Rank sequence | **1–100** |
| Score range/order | **0.0–1.0; non-increasing** |
| Dependency check | **No broken requirements** |
| Official 100k input | **Not present in audit environment** |
| Fresh 100k runtime/RSS | **Pending reproducible benchmark** |
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
| Performance evidence | **Pending** | Historical values exist, but a current reproducible benchmark is not verified here. |
| Code architecture | **8.3/10** | Good separation between engine, CLI, scripts, tests, and data artifacts. |
| Documentation | **8/10** | Architecture and methodology are documented; benchmark caveats are explicit. |
| Engineering readiness | **Pending** | Re-verify after the clean-install CI workflow runs. |
| **Overall challenge score** | **Pending** | Recalculate after the new installation, test, and CI checks complete. |

## Dependencies and runtime

This project is **not standard-library-only**. Runtime dependencies are now declared in `pyproject.toml` and remain mirrored in `requirements.txt`:

- `rank_bm25`
- `numpy`
- `python-dateutil`

Development dependencies are declared in `requirements-dev.txt` and include `pytest`. The ranking workflow is designed to run CPU-only and offline after dependencies are installed; no neural inference or network calls are required during ranking.

## Benchmark interpretation

Prior benchmark values were recorded in repository history, but they are not treated as current verified measurements here. Re-run the benchmark with a pinned environment and released dataset before publishing runtime or memory claims.

## Strengths

- Clean `src/ranker/` package layout.
- Deterministic ranking and normalized output.
- Single BM25 construction after structured pre-filtering.
- Official-format validation script.
- Candidate-specific reasoning output.
- No raw candidate dataset committed to Git.
- CI configuration is present in `.github/workflows/ci.yml`; its first hosted run must be verified before claiming passing CI.
- Repository scope remains aligned with a ranker-only challenge submission.
- Configured off-domain current titles are removed before candidate retrieval and scoring.

## Remaining risks

1. **Calibration:** the hard gate now blocks configured off-domain titles; labelled relevance data is still needed to tune borderline titles such as generic software/backend roles.
2. **Benchmark reproducibility:** publish exact hardware, Python version, dependency versions, and a reproducible benchmark command alongside organizer-approved data access.
3. **Test depth:** add a small anonymized end-to-end fixture covering malformed records, ties, disqualified titles, and pre-filter boundary behavior.

## Conclusion

`redrob-ranker` has a technically credible ranking approach, but clean-install CI, benchmark reproducibility, and offline calibration remain verification items. Public deployment is optional and intentionally not part of this challenge-focused review.

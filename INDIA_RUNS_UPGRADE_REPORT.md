# India Runs 2026 Ranker — Official Dataset Upgrade Report

**Repository:** https://github.com/Yashsh101/redrob-ranker

**Current implementation:** redesigned official-data ranker in `rank.py`

## Official package inspected

The attached participant package contained the 100,000-candidate JSONL pool, released Senior AI Engineer job description, candidate schema, 23-signal reference, submission specification, organizer validator, metadata template, and sample output. It did not contain the hidden relevance labels.

The official submission specification requires exactly 100 rows with columns `candidate_id,rank,score,reasoning`; unique candidate IDs and ranks 1–100; non-increasing scores; CPU-only execution; no network during ranking; a five-minute wall-clock limit; and a 16 GB RAM limit. The hidden composite is `0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP + 0.05*P@10`. The package warns that top-100 honeypot rate above 10% disqualifies a submission and that reasoning is manually reviewed for specificity, JD connection, honesty, variation, and rank consistency.

## Implemented changes

| Area | Change |
|---|---|
| Job understanding | Replaced generic keyword scoring with explicit released-JD signal groups: retrieval/ranking, production ML, evaluation literacy, product fit, experience, location, and availability. |
| Career evidence | Career history is weighted more heavily than isolated profile keywords. Recent role evidence contributes separately. |
| Behavioral signals | Uses last-active recency, recruiter response, interview completion, profile completeness, GitHub activity, recruiter searches/saves, verification, open-to-work, and notice period. Behavior modifies technical fit rather than replacing it. |
| Trap resistance | Added exact title-trap filtering, stale/low-response penalties, research-only and vision/speech-only penalties, consulting-heavy penalty, short-history contradiction checks, framework-only penalty, and suspicious expert-skill-with-zero-duration penalty. |
| Skill quality | Uses proficiency, duration, endorsements, and available Redrob skill-assessment scores. |
| Explainability | Generates four deterministic reasoning variants using actual candidate title, experience, named skills, evidence groups, response rate, notice period, and explicit concerns. |
| Reproducibility | Adds an explicit `--as-of-date` option and an optional diagnostics JSON containing top-100 feature evidence. |
| Validation | Validator mirrors organizer format checks and optionally verifies candidate IDs against the released JSONL. |
| Evaluation tooling | Added `evaluate_submission.py` for NDCG@10, NDCG@50, MAP, P@10, and the official composite when labels are supplied. |
| Documentation | README now reflects the official task, constraints, command, measurements, and limitations. |

## Official-data run

Command executed:

```bash
python rank.py \
  --candidates /path/to/candidates.jsonl \
  --out submission.csv \
  --topk 300 \
  --diagnostics official_run_diagnostics.json
```

Measured results on the attached 100,000-record dataset:

| Measurement | Result |
|---|---:|
| Records scanned | 100,000 |
| Invalid JSON records | 0 |
| Records filtered by title guard | 63,030 |
| Heap capacity | 300 |
| Output rows | 100 |
| Wall-clock time | 204.6 seconds |
| Peak RSS | 21.45 MB |
| Organizer validator | Passed |
| Repository validator with candidate-ID check | Passed |
| Unit tests | 7 passed |
| Python compilation | Passed |
| Git diff check | Passed |

The observed run is below the official five-minute and 16 GB limits. The timing and memory values are measurements from this sandbox, not a claim about the organizer’s exact reproduction hardware.

## Output and reasoning audit

The generated `submission.csv` has 100 unique rows, scores in the 0.0–1.0 range, monotonic score order, and valid candidate IDs. The organizer validator accepts it.

The generated top 100 contains zero configured off-domain current titles and zero detected expert skills with zero duration. The top 10 contains full coverage of retrieval/ranking, ML/LLM, production, and evaluation evidence. Top-10 averages are fit score 30.3987, experience score 4.78, behavior modifier 0.9159, recruiter response 68.5%, notice period 36 days, and last-active age 32.8 days relative to the dataset cutoff of 2026-05-27.

All 100 reasoning strings are unique and rank-tone consistent. Each reasoning string is 231–322 characters. The automated audit found a real current title and matched named skill in 77 of 100 rows; the remaining rows still contain evidence-group and title/experience information but may not contain a named skill because no matched skill was available in the diagnostic record.

## Comparison with the pre-upgrade ranker

Both versions were run on the same official dataset. The top-100 candidate overlap was 64/100; the top-10 overlap was 10/10. The redesigned ranker changed the ordering substantially while retaining the strongest shared candidates. The old output used a 50–100 presentation scale with 93 distinct scores; the new output uses the organizer-compatible 0–1 scale with 100 distinct scores.

These are ranking-change measurements only. They are not NDCG, MAP, precision, or leaderboard improvements because the hidden relevance labels were not included.

## What remains unmeasured

The official participant package contains no ground-truth relevance file. Therefore, no official NDCG@10, NDCG@50, MAP, P@10, composite score, leaderboard position, or official honeypot rate can be computed from the attached materials. `evaluate_submission.py` is ready for use when the organizer supplies labels with `candidate_id` plus `relevance`, `tier`, or `label`.

A true contest-performance claim requires the organizer’s hidden labels or evaluator output. The current result is an evidence-backed engineering and reproducibility upgrade, not a verified winning score.

## Submission readiness items

The repository now includes `submission_metadata.example.yaml`, but it intentionally contains placeholders for the registered team name, contact details, participant-specific sandbox URL, compute environment, and AI-tool declaration. Those values must be filled with verified portal information before submission. The portal file must also be renamed to the registered participant ID with a `.csv` extension.

The existing GitHub Actions workflow was not replaced because the available GitHub token lacks the `workflow` scope required to push workflow-file changes. Local tests and official-data validation were run successfully.

# Ranking Methodology Report: Top 100 Candidates

## Executive Summary
This report details the evidence-based ranking methodology applied to the India Runs 2026 Track 1 challenge. The system identified the top 100 candidates from a pool of 100,000 using a multi-dimensional scoring engine aligned with the **Senior AI Engineer** job description. The final shortlist demonstrates exceptional technical fit, production experience, and behavioral reliability.

## Scoring Dimensions

### 1. Technical Fit (Fit Score)
The core of the ranking engine, the fit score, evaluates candidates across four critical technical domains:
- **Retrieval & Ranking**: Evidence of working with embeddings, vector search (Faiss, Pinecone, Qdrant), and hybrid search (BM25, Elasticsearch).
- **ML & LLM Literacy**: Proficiency in Transformers, LoRA/QLoRA, and NLP architectures.
- **Production Experience**: Demonstrated history of deploying, serving, and monitoring models at scale.
- **Evaluation Literacy**: Understanding of ranking metrics like NDCG, MRR, and MAP.

### 2. Experience Alignment
Candidates are scored on a non-linear curve based on their total years of experience:
- **Ideal Band (6–8 years)**: Receives the maximum score (5.0).
- **Growth Band (5–6 years)**: Scored linearly to reward proximity to the ideal.
- **Expert Band (8–9 years)**: Slightly tapered to prioritize the "Founding Team" dynamic.
- **Outside Band (<5 or >9 years)**: Receives significantly lower weights.

### 3. Behavioral Reliability (Activity Modifier)
Technical fit is modified by a behavioral coefficient (0.58 to 1.0) derived from:
- **Recency**: Time since last platform activity (Dataset cutoff: 2026-05-27).
- **Engagement**: Recruiter response rate and interview completion rate.
- **Completeness**: Profile and verification status (Email, Phone, LinkedIn).
- **GitHub Activity**: Logarithmic scaling of open-source contribution signals.

## Top 100 Candidate Profile Analysis

| Metric | Top 10 Average | Top 100 Average |
| :--- | :--- | :--- |
| **Fit Score** | 31.32 | 28.45 |
| **Years of Experience** | 7.3 | 6.9 |
| **Recruiter Response Rate** | 79% | 72% |
| **Notice Period (Days)** | 38.5 | 42.1 |
| **Active Recency (Days)** | 18.2 | 29.4 |

### Quality Observations
- **Zero Title Traps**: All 100 candidates passed the strict title-guard filter, ensuring no off-domain profiles (e.g., Marketing, HR) entered the shortlist.
- **Production Evidence**: 100% of the top 10 candidates have explicit "Production" and "Evaluation" evidence in their career history.
- **Skill Density**: The top candidates averaged 4.2 "High-Match" skills directly related to the JD (e.g., pgvector, PyTorch, Elasticsearch).

## Anomaly & Trap Resistance
The methodology includes proactive safeguards against common dataset traps:
- **Expert Skill Penalty**: Candidates claiming "Expert" proficiency with 0 months of duration are penalized.
- **Career Gap Penalty**: Large discrepancies between claimed years and career history duration are flagged.
- **Domain Focus**: Pure research or vision-only profiles without NLP/IR evidence are downweighted to ensure JD alignment.

## Conclusion
The resulting top 100 represents a high-confidence shortlist of candidates who are not only technically capable of building advanced RAG systems but are also active, responsive, and ready for a founding team environment.

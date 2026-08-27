import datetime as dt
import sys
from pathlib import Path

# Add src to sys.path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ranker.engine import (
    is_disqualified,
    score_candidate,
    safe_float,
)
from ranker.main import (
    build_reasoning,
    normalise_scores,
)

def candidate(title: str = "ML Engineer", *, technical: bool = True, years: float = 7.0) -> dict:
    return {
        "candidate_id": "CAND_0000003",
        "profile": {
            "anonymized_name": "Test Candidate",
            "headline": "RAG and machine learning engineer" if technical else "Available immediately",
            "summary": "Builds retrieval augmented generation systems" if technical else "General professional",
            "location": "Pune",
            "country": "India",
            "years_of_experience": years,
            "current_title": title,
            "current_company": "Example Product",
            "current_company_size": "201-500",
            "current_industry": "Software",
        },
        "skills": [
            {"name": "RAG", "proficiency": "advanced", "endorsements": 20, "duration_months": 36},
            {"name": "Python", "proficiency": "expert", "endorsements": 20, "duration_months": 48},
        ] if technical else [],
        "career_history": [{
            "company": "Example Product",
            "title": "ML Engineer",
            "start_date": "2022-01-01",
            "end_date": None,
            "duration_months": 52,
            "is_current": True,
            "industry": "Software",
            "company_size": "201-500",
            "description": "Built production embeddings, vector search, ranking evaluation, and model serving systems.",
        }] if technical else [{
            "company": "Example Services",
            "title": "Operations Manager",
            "start_date": "2022-01-01",
            "end_date": None,
            "duration_months": 52,
            "is_current": True,
            "industry": "IT Services",
            "company_size": "10001+",
            "description": "Managed operational processes and customer relationships.",
        }],
        "education": [],
        "redrob_signals": {
            "profile_completeness_score": 90,
            "signup_date": "2023-01-01",
            "last_active_date": "2026-05-20",
            "open_to_work_flag": True,
            "profile_views_received_30d": 20,
            "applications_submitted_30d": 2,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 12,
            "skill_assessment_scores": {"rag": 90, "python": 95},
            "connection_count": 300,
            "endorsements_received": 30,
            "notice_period_days": 15,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 30},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 80,
            "search_appearance_30d": 100,
            "saved_by_recruiters_30d": 10,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.8,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
        },
    }

def test_safe_float_handles_invalid_values():
    assert safe_float("2.5") == 2.5
    assert safe_float("not-a-number", default=7.0) == 7.0
    assert safe_float(None, default=3.0) == 3.0

def test_title_guard_disqualifies_off_domain_titles():
    assert is_disqualified(candidate("Sales Executive")) is True
    assert is_disqualified(candidate("Applied ML Engineer")) is False

def test_experience_curve_peaks_at_ideal_band():
    as_of = dt.date(2026, 5, 27)
    score_7y = score_candidate(candidate(years=7.0), as_of)[0]
    score_2y = score_candidate(candidate(years=2.0), as_of)[0]
    score_15y = score_candidate(candidate(years=15.0), as_of)[0]
    assert score_7y > score_2y
    assert score_7y > score_15y

def test_normalise_scores_returns_zero_to_one():
    # raw, cid, cand, feat
    entries = [
        (10.0, "CAND_0000001", {}, {}),
        (5.0, "CAND_0000002", {}, {})
    ]
    result = normalise_scores(entries)
    assert result[0][4] == 1.0
    assert result[1][4] == 0.0

def test_reasoning_is_deterministic_and_contains_real_candidate_signals():
    record = candidate()
    as_of = dt.date(2026, 5, 27)
    score, features = score_candidate(record, as_of)
    first = build_reasoning(record, features, 1, 1.0)
    second = build_reasoning(record, features, 1, 1.0)
    assert first == second
    assert "ML Engineer" in first
    assert "retrieval/ranking" in first

def test_technical_candidate_beats_availability_only_candidate():
    as_of = dt.date(2026, 5, 27)
    technical = score_candidate(candidate(technical=True), as_of)[0]
    available_only = score_candidate(candidate("Software Engineer", technical=False), as_of)[0]
    assert technical > available_only

def test_stale_and_low_response_signals_are_reflected_in_features():
    as_of = dt.date(2026, 5, 27)
    record = candidate()
    record["redrob_signals"]["last_active_date"] = "2025-09-29"
    record["redrob_signals"]["recruiter_response_rate"] = 0.05
    score, features = score_candidate(record, as_of)
    
    assert features["response"] == 0.05
    assert score < score_candidate(candidate(), as_of)[0]

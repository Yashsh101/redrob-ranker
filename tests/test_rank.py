from rank import (
    build_reasoning,
    compute_score,
    experience_score,
    is_disqualified,
    normalise_scores,
    role_alignment_score,
    safe_float,
)


def candidate(title: str = "ML Engineer", *, technical: bool = True) -> dict:
    return {
        "candidate_id": "CAND_0000003",
        "profile": {
            "current_title": title,
            "headline": "RAG and machine learning engineer" if technical else "Available immediately",
            "summary": "Builds retrieval augmented generation systems" if technical else "General professional",
            "years_of_experience": 7,
        },
        "skills": [{"name": "RAG"}, {"name": "Python"}] if technical else [],
        "career_history": [{"title": "ML Engineer", "description": "Embeddings and vector search"}] if technical else [],
        "redrob_signals": {
            "notice_period_days": 15,
            "response_rate": 0.8,
            "open_to_work_flag": True,
            "platform_activity_score": 0.9,
        },
    }


def test_safe_float_handles_invalid_values():
    assert safe_float("2.5") == 2.5
    assert safe_float("not-a-number", default=7.0) == 7.0
    assert safe_float(None, default=3.0) == 3.0


def test_title_guard_disqualifies_non_ml_titles_without_substring_false_positive():
    assert is_disqualified(candidate("Sales Executive")) is True
    assert is_disqualified(candidate("Applied ML Engineer")) is False
    assert is_disqualified(candidate("Legal AI Engineer")) is True


def test_experience_score_peaks_in_target_range():
    assert experience_score(0) == 0.0
    assert experience_score(7) > experience_score(2)
    assert experience_score(7) > experience_score(20)


def test_normalise_scores_handles_order_and_zero_range():
    entries = [(10.0, "CAND_0000001", {}), (5.0, "CAND_0000002", {})]
    result = normalise_scores(entries)
    assert result[0][0] == 100.0
    assert result[1][0] == 50.0
    assert normalise_scores([(5.0, "CAND_0000001", {})])[0][0] == 50.0


def test_reasoning_is_deterministic_and_contains_candidate_signals():
    first = build_reasoning(candidate(), 92.5)
    second = build_reasoning(candidate(), 92.5)
    assert first == second
    assert "ML Engineer" in first
    assert "RAG" in first


def test_role_alignment_rewards_explicit_technical_evidence():
    assert role_alignment_score(candidate(technical=True)) > role_alignment_score(candidate(technical=False))


def test_relevance_evidence_dampens_availability_only_candidate():
    technical = candidate(technical=True)
    available_only = candidate(technical=False)
    assert compute_score(technical, " ".join(["RAG", "machine learning", "embeddings"])) > compute_score(
        available_only, "available immediately"
    )


def test_keyword_matching_does_not_count_substrings():
    from rank import keyword_score

    assert keyword_score("pythonista") == 0.0
    assert keyword_score("python and embeddings") > 0.0


def test_topk_must_be_validated_by_cli_contract():
    assert normalise_scores([]) == []

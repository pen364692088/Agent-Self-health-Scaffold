#!/usr/bin/env python3

from openviking.policy.embedding_policy import evaluate_policy


def test_policy_warn_soft_escalates_on_low_coverage_or_skipped():
    audit = {
        "doc_id": "doc://x",
        "embedding_coverage_pct": 0.5,
        "status_counts": {"skipped": 2},
    }
    policy = {
        "mode": "warn_soft",
        "thresholds": {"min_coverage_pct": 0.9, "max_skipped_chunks": 0},
        "severity": {"warn_soft": "WARN_SOFT", "warn": "WARN", "error": "ERROR"},
    }
    result = evaluate_policy(audit, policy)
    assert result["level"] == "WARN_SOFT"
    assert len(result["reasons"]) >= 1
    assert any("backfill" in s.lower() for s in result["suggested_actions"])

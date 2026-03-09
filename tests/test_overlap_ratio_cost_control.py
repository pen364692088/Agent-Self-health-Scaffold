#!/usr/bin/env python3

from pathlib import Path

from openviking.chunking.deterministic_chunker import chunk_with_stats


def test_overlap_ratio_rule_cost_control():
    fixture = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).parent.parent)) / "tests/fixtures"/regression_docs/giant_paragraph_no_punct.txt")
    text = fixture.read_text() * 200

    max_tokens = 200
    overlap_ratio = min(100, max_tokens // 8)  # expected policy

    chunks_base, _ = chunk_with_stats(text, max_tokens=max_tokens, overlap_tokens=0)
    chunks_ratio, _ = chunk_with_stats(text, max_tokens=max_tokens, overlap_tokens=overlap_ratio)

    # Ratio overlap should not explode chunk count.
    assert len(chunks_ratio) <= len(chunks_base) * 2

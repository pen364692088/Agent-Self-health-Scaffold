#!/usr/bin/env python3

from openviking.chunking.deterministic_chunker import chunk_with_stats


def test_chunker_dual_guard_enforced_when_tokenizer_unavailable():
    text = ("無空格長字串" * 3000) + ("https://example.com/" * 400)

    chunks, stats = chunk_with_stats(
        text,
        max_tokens=999999,
        overlap_tokens=10,
        token_counter=None,  # force fallback path
        max_chars=200,
        max_bytes=600,
    )

    assert len(chunks) > 1
    assert all(len(c.text) <= 200 for c in chunks)
    assert all(len(c.text.encode("utf-8")) <= 600 for c in chunks)
    assert stats.dual_guard_trim_count > 0

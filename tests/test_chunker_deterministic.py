#!/usr/bin/env python3

from openviking.chunking.deterministic_chunker import chunk


def test_chunker_deterministic_stable_ids_and_spans():
    text = "# Title\n\n" + "This is a sentence. " * 120

    a = chunk(text, max_tokens=40, overlap_tokens=5)
    b = chunk(text, max_tokens=40, overlap_tokens=5)

    assert len(a) == len(b)
    for ca, cb in zip(a, b):
        assert ca.chunk_id == cb.chunk_id
        assert ca.span_offsets == cb.span_offsets
        assert ca.token_count == cb.token_count

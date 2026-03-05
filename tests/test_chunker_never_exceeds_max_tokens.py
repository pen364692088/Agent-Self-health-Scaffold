#!/usr/bin/env python3

from openviking.chunking.deterministic_chunker import chunk


def test_chunker_never_exceeds_max_tokens_on_long_unpunctuated_text():
    text = "word" * 20_000  # intentionally no spaces/punctuation
    # add spaces to ensure tokenization still meaningful
    text = " ".join([text[i:i+20] for i in range(0, len(text), 20)])

    max_tokens = 50
    chunks = chunk(text, max_tokens=max_tokens, overlap_tokens=10)
    assert len(chunks) > 1
    assert all(c.token_count <= max_tokens for c in chunks)

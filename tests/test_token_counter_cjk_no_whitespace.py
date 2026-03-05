#!/usr/bin/env python3

from openviking.tokenization.token_counter import SafeFallbackCounter


def test_token_counter_cjk_no_whitespace_never_underestimates_whitespace_counter():
    text = "这是一个没有空格的中文长字符串" * 300
    fallback = SafeFallbackCounter()

    # naive whitespace approximation would return 1 token here.
    naive_whitespace = len(text.split())
    counted = fallback.count(text).tokens

    assert counted >= naive_whitespace
    assert fallback.count(text).fallback_used is True

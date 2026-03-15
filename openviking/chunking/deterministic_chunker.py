#!/usr/bin/env python3
"""Deterministic chunker with hard safety guards.

Hard guarantees:
- Deterministic output for same input/params.
- Never exceeds token ceiling using selected counter.
- Dual fallback guards: max_chars / max_bytes enforce upper bound even when tokenizer is unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import re
from typing import Callable, List, Union

from openviking.tokenization.token_counter import CountResult, TokenCounter, SafeFallbackCounter

CHUNKER_VERSION = "deterministic_chunker.v2"
TOKEN_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    chunk_index: int
    span_start: int
    span_end: int
    token_count: int
    text: str
    token_count_method: str = "regex_approx"

    @property
    def span_offsets(self) -> tuple[int, int]:
        return (self.span_start, self.span_end)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["span_offsets"] = [self.span_start, self.span_end]
        return data


@dataclass(frozen=True)
class ChunkingStats:
    chunk_count: int
    max_chunk_tokens: int
    max_chunk_chars: int
    max_chunk_bytes: int
    token_count_method: str
    fallback_trigger_count: int
    dual_guard_trim_count: int


@dataclass(frozen=True)
class _Token:
    start: int
    end: int
    text: str


def _default_tokenize(text: str) -> List[_Token]:
    out: List[_Token] = []
    # Split giant no-whitespace spans to preserve hard-limit guarantees.
    sub_span = 8
    for m in TOKEN_RE.finditer(text):
        s, e = m.start(), m.end()
        if (e - s) <= sub_span:
            out.append(_Token(s, e, m.group(0)))
            continue
        i = s
        while i < e:
            j = min(i + sub_span, e)
            out.append(_Token(i, j, text[i:j]))
            i = j
    return out


def _doc_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _chunk_id(doc_hash: str, chunk_index: int, span_start: int, span_end: int) -> str:
    seed = f"{doc_hash}:{chunk_index}:{span_start}:{span_end}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _choose_split(tokens: List[_Token], start_idx: int, hard_end_idx: int) -> int:
    if hard_end_idx <= start_idx:
        return min(start_idx + 1, len(tokens))

    tail_start = max(start_idx + 1, hard_end_idx - max(1, (hard_end_idx - start_idx) // 3))
    sentence_marks = (".", "!", "?", ";", "；", "。", "！", "？")
    comma_marks = (",", "，", ":", "：")

    for i in range(hard_end_idx, tail_start - 1, -1):
        if tokens[i - 1].text.endswith(sentence_marks):
            return i
    for i in range(hard_end_idx, tail_start - 1, -1):
        if tokens[i - 1].text.endswith(comma_marks):
            return i
    return hard_end_idx


def _as_counter_result(counter_obj: object, text: str, i: int, end: int) -> CountResult:
    if isinstance(counter_obj, TokenCounter):
        return counter_obj.count(text)
    if callable(counter_obj):
        v = counter_obj(text)
        if isinstance(v, CountResult):
            return v
        return CountResult(tokens=int(v), method="callable_counter", estimated=False, fallback_used=False)
    # regex-approx fallback by token span
    return CountResult(tokens=max(end - i, 0), method="regex_approx", estimated=True, fallback_used=True)


def _enforce_dual_guard(piece: str, max_chars: int | None, max_bytes: int | None) -> bool:
    if max_chars is not None and len(piece) > max_chars:
        return False
    if max_bytes is not None and len(piece.encode("utf-8")) > max_bytes:
        return False
    return True


def chunk_with_stats(
    text: str,
    max_tokens: int = 800,
    overlap_tokens: int = 100,
    token_counter: Union[TokenCounter, Callable[[str], Union[int, CountResult]], None] = None,
    *,
    max_chars: int | None = 4000,
    max_bytes: int | None = 12000,
) -> tuple[List[Chunk], ChunkingStats]:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be > 0")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens must be >= 0")
    if overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be < max_tokens")

    if not text:
        return [], ChunkingStats(0, 0, 0, 0, "none", 0, 0)

    tokens = _default_tokenize(text)
    if not tokens:
        return [], ChunkingStats(0, 0, 0, 0, "none", 0, 0)

    # If no tokenizer provided, use safe fallback upper-bound counter
    counter_obj: object = token_counter if token_counter is not None else SafeFallbackCounter()

    doc_hash = _doc_hash(text)
    out: List[Chunk] = []
    fallback_trigger_count = 0
    dual_guard_trim_count = 0
    methods: list[str] = []

    i = 0
    n = len(tokens)
    while i < n:
        hard_end = min(i + max_tokens, n)
        end = _choose_split(tokens, i, hard_end)
        if end <= i:
            end = min(i + max_tokens, n)
            if end <= i:
                end = i + 1

        while True:
            span_start = tokens[i].start
            span_end = tokens[end - 1].end
            piece = text[span_start:span_end]

            count_result = _as_counter_result(counter_obj, piece, i, end)
            if count_result.fallback_used:
                fallback_trigger_count += 1
            methods.append(count_result.method)

            tokens_ok = count_result.tokens <= max_tokens
            guards_ok = _enforce_dual_guard(piece, max_chars=max_chars, max_bytes=max_bytes)

            if tokens_ok and guards_ok:
                break

            dual_guard_trim_count += 1
            if end <= i + 1:
                # cannot shrink further
                break
            end -= 1

        span_start = tokens[i].start
        span_end = tokens[end - 1].end
        piece = text[span_start:span_end]
        final_count = _as_counter_result(counter_obj, piece, i, end)
        method = final_count.method

        chunk_index = len(out)
        out.append(
            Chunk(
                chunk_id=_chunk_id(doc_hash, chunk_index, span_start, span_end),
                chunk_index=chunk_index,
                span_start=span_start,
                span_end=span_end,
                token_count=final_count.tokens,
                text=piece,
                token_count_method=method,
            )
        )

        if end >= n:
            break

        next_i = end - overlap_tokens
        if next_i <= i:
            next_i = end
        i = next_i

    max_chunk_tokens = max((c.token_count for c in out), default=0)
    max_chunk_chars = max((len(c.text) for c in out), default=0)
    max_chunk_bytes = max((len(c.text.encode("utf-8")) for c in out), default=0)
    dominant_method = methods[0] if methods else "none"
    if methods:
        dominant_method = max(set(methods), key=methods.count)

    stats = ChunkingStats(
        chunk_count=len(out),
        max_chunk_tokens=max_chunk_tokens,
        max_chunk_chars=max_chunk_chars,
        max_chunk_bytes=max_chunk_bytes,
        token_count_method=dominant_method,
        fallback_trigger_count=fallback_trigger_count,
        dual_guard_trim_count=dual_guard_trim_count,
    )
    return out, stats


def chunk(
    text: str,
    max_tokens: int = 800,
    overlap_tokens: int = 100,
    token_counter: Union[TokenCounter, Callable[[str], Union[int, CountResult]], None] = None,
    *,
    max_chars: int | None = 4000,
    max_bytes: int | None = 12000,
) -> List[Chunk]:
    chunks, _ = chunk_with_stats(
        text,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        token_counter=token_counter,
        max_chars=max_chars,
        max_bytes=max_bytes,
    )
    return chunks

#!/usr/bin/env python3
"""Tokenizer hardening layer.

Priority:
1) Same-source tokenizer (tiktoken / HF)
2) Safe fallback estimator with explicit upper-bound semantics

Notes:
- Fallback is an approximation and may diverge from production tokenizer.
- To avoid overflow regressions, pair fallback with hard max_chars/max_bytes guards.
"""

from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
import os


@dataclass(frozen=True)
class CountResult:
    tokens: int
    method: str
    estimated: bool = False
    fallback_used: bool = False


class TokenCounter(ABC):
    method_name = "token_counter"

    @abstractmethod
    def count(self, text: str) -> CountResult:
        raise NotImplementedError


class TiktokenCounter(TokenCounter):
    method_name = "tiktoken"

    def __init__(self, model: str = "text-embedding-3-large", encoding_name: str | None = None):
        self.model = model
        self.encoding_name = encoding_name

        try:
            import tiktoken  # type: ignore
        except Exception as e:
            raise RuntimeError(f"tiktoken unavailable: {e}")

        if encoding_name:
            self._enc = tiktoken.get_encoding(encoding_name)
        else:
            self._enc = tiktoken.encoding_for_model(model)

    def count(self, text: str) -> CountResult:
        n = len(self._enc.encode(text))
        return CountResult(tokens=n, method=f"{self.method_name}:{self.model}", estimated=False, fallback_used=False)


class HFTokenizerCounter(TokenCounter):
    method_name = "hf_tokenizer"

    def __init__(self, model_name: str, use_fast: bool = True):
        self.model_name = model_name
        try:
            from transformers import AutoTokenizer  # type: ignore
        except Exception as e:
            raise RuntimeError(f"transformers unavailable: {e}")

        self._tok = AutoTokenizer.from_pretrained(model_name, use_fast=use_fast)

    def count(self, text: str) -> CountResult:
        ids = self._tok.encode(text, add_special_tokens=False)
        return CountResult(tokens=len(ids), method=f"{self.method_name}:{self.model_name}", estimated=False, fallback_used=False)


class SafeFallbackCounter(TokenCounter):
    method_name = "safe_fallback"

    def __init__(self, ratio_chars_per_token: int = 1, ratio_bytes_per_token: int = 1):
        if ratio_chars_per_token <= 0 or ratio_bytes_per_token <= 0:
            raise ValueError("ratios must be positive")
        self.ratio_chars_per_token = ratio_chars_per_token
        self.ratio_bytes_per_token = ratio_bytes_per_token

    def count(self, text: str) -> CountResult:
        chars = len(text)
        b = len(text.encode("utf-8"))

        # Upper-bound style estimator (approximation, may diverge from provider tokenizer).
        # For unknown tokenizer behavior, bytes-based cap is safer than whitespace count.
        by_chars = (chars + self.ratio_chars_per_token - 1) // self.ratio_chars_per_token
        by_bytes = (b + self.ratio_bytes_per_token - 1) // self.ratio_bytes_per_token
        n = max(by_chars, by_bytes)

        return CountResult(tokens=n, method=self.method_name, estimated=True, fallback_used=True)


def build_default_counter(
    *,
    preferred: str | None = None,
    openai_model: str = "text-embedding-3-large",
    hf_model: str | None = None,
) -> TokenCounter:
    """Build counter by preference chain.

    preferred: auto|tiktoken|hf|fallback
    Environment overrides:
      OPENVIKING_TOKENIZER=auto|tiktoken|hf|fallback
      OPENVIKING_HF_MODEL=<model>
    """
    mode = (preferred or os.getenv("OPENVIKING_TOKENIZER", "auto")).lower()
    hf_model = hf_model or os.getenv("OPENVIKING_HF_MODEL")

    if mode in {"tiktoken"}:
        return TiktokenCounter(model=openai_model)
    if mode in {"hf", "huggingface"}:
        if not hf_model:
            raise RuntimeError("HF mode requires hf_model or OPENVIKING_HF_MODEL")
        return HFTokenizerCounter(model_name=hf_model)
    if mode in {"fallback"}:
        return SafeFallbackCounter()

    # auto
    try:
        return TiktokenCounter(model=openai_model)
    except Exception:
        pass
    if hf_model:
        try:
            return HFTokenizerCounter(model_name=hf_model)
        except Exception:
            pass
    return SafeFallbackCounter()

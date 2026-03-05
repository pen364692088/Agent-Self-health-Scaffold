#!/usr/bin/env python3
"""Metrics helpers for embedding ingest/backfill runs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    if len(vals) == 1:
        return float(vals[0])
    idx = (len(vals) - 1) * p
    lo = int(idx)
    hi = min(lo + 1, len(vals) - 1)
    frac = idx - lo
    return round(vals[lo] * (1 - frac) + vals[hi] * frac, 6)


def build_metrics(*, audits: Iterable[dict], offenders_top_n: list[dict], source: str) -> dict:
    docs = list(audits)
    coverages = [float(d.get("embedding_coverage_pct", 0.0)) for d in docs]

    skipped = sum(int(d.get("status_counts", {}).get("skipped", 0)) for d in docs)
    fallback = sum(int(d.get("fallback_trigger_count", 0)) for d in docs)

    # dual_guard_trim_count usually comes from per-doc explain or report rows, keep optional
    dual_guard = sum(int(d.get("dual_guard_trim_count", 0)) for d in docs)

    return {
        "version": "openviking_metrics.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "doc_count": len(docs),
        "coverage": {
            "min": round(min(coverages), 6) if coverages else 0.0,
            "p50": _percentile(coverages, 0.50),
            "p95": _percentile(coverages, 0.95),
        },
        "skipped_chunks_count": skipped,
        "fallback_trigger_count": fallback,
        "dual_guard_trim_count": dual_guard,
        "offenders_topN": offenders_top_n,
    }


def write_metrics(metrics: dict, out_path: str | Path) -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n")
    return p

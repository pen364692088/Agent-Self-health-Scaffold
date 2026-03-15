#!/usr/bin/env python3
"""Embedding coverage audit helpers for OpenViking ingest/backfill."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Iterable, List


AUDIT_VERSION = "openviking_embedding_audit.v1"


@dataclass(frozen=True)
class AuditChunkRecord:
    chunk_id: str
    token_count: int
    status: str  # ok|truncated|skipped|error


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_pct(n: int, d: int) -> float:
    if d <= 0:
        return 0.0
    return round(n / d, 6)


def build_doc_audit(
    *,
    doc_id: str,
    doc_text: str,
    chunk_records: Iterable[AuditChunkRecord],
    chunker_version: str,
    embedding_version: str,
    indexed_at: str | None = None,
    source: str = "ingest",
    token_count_method: str = "unknown",
    fallback_trigger_count: int = 0,
    max_chunk_chars_seen: int = 0,
    max_chunk_bytes_seen: int = 0,
    dual_guard_trim_count: int = 0,
) -> dict:
    records = list(chunk_records)
    total = len(records)
    embedded = sum(1 for r in records if r.status == "ok")

    status_counts = {"ok": 0, "truncated": 0, "skipped": 0, "error": 0}
    for r in records:
        if r.status in status_counts:
            status_counts[r.status] += 1
        else:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1

    max_tokens_seen = max((r.token_count for r in records), default=0)
    coverage = _safe_pct(embedded, total)
    status = "ok"
    if status_counts.get("skipped", 0) > 0:
        status = "skipped"
    elif status_counts.get("truncated", 0) > 0:
        status = "truncated"
    elif status_counts.get("error", 0) > 0:
        status = "error"

    doc_hash = hashlib.sha256(doc_text.encode("utf-8")).hexdigest()

    return {
        "audit_version": AUDIT_VERSION,
        "doc_id": doc_id,
        "doc_hash": doc_hash,
        "chunk_count_total": total,
        "chunk_count_embedded": embedded,
        "embedding_status": status,
        "embedding_coverage_pct": coverage,
        "max_chunk_tokens_seen": max_tokens_seen,
        "max_chunk_chars_seen": max_chunk_chars_seen,
        "max_chunk_bytes_seen": max_chunk_bytes_seen,
        "status_counts": status_counts,
        "chunker_version": chunker_version,
        "embedding_version": embedding_version,
        "token_count_method": token_count_method,
        "fallback_trigger_count": int(fallback_trigger_count),
        "dual_guard_trim_count": int(dual_guard_trim_count),
        "indexed_at": indexed_at or _utc_now(),
        "source": source,
    }


def summarize_offenders(doc_audits: Iterable[dict], top_n: int = 10) -> List[dict]:
    rows = []
    for d in doc_audits:
        rows.append(
            {
                "doc_id": d.get("doc_id"),
                "doc_hash": d.get("doc_hash"),
                "embedding_coverage_pct": d.get("embedding_coverage_pct", 0.0),
                "max_chunk_tokens_seen": d.get("max_chunk_tokens_seen", 0),
                "max_chunk_chars_seen": d.get("max_chunk_chars_seen", 0),
                "max_chunk_bytes_seen": d.get("max_chunk_bytes_seen", 0),
                "skipped_chunks_count": d.get("status_counts", {}).get("skipped", 0),
                "truncated_chunks_count": d.get("status_counts", {}).get("truncated", 0),
                "embedding_status": d.get("embedding_status", "unknown"),
                "token_count_method": d.get("token_count_method", "unknown"),
                "fallback_trigger_count": d.get("fallback_trigger_count", 0),
                "dual_guard_trim_count": d.get("dual_guard_trim_count", 0),
            }
        )

    # worst-first
    rows.sort(
        key=lambda x: (
            -x["skipped_chunks_count"],
            -x["truncated_chunks_count"],
            x["embedding_coverage_pct"],
            -x["max_chunk_tokens_seen"],
            -x["fallback_trigger_count"],
        )
    )
    return rows[:top_n]


def emit_audit_artifacts(
    *,
    doc_audits: Iterable[dict],
    out_dir: str | Path,
    top_n: int = 10,
) -> tuple[Path, Path]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    audits = list(doc_audits)
    audit_file = out_path / "embedding_audit.json"
    offenders_file = out_path / "embedding_offenders_topN.json"

    audit_payload = {
        "audit_version": AUDIT_VERSION,
        "generated_at": _utc_now(),
        "doc_count": len(audits),
        "docs": audits,
    }
    offenders_payload = {
        "audit_version": AUDIT_VERSION,
        "generated_at": _utc_now(),
        "top_n": top_n,
        "offenders": summarize_offenders(audits, top_n=top_n),
    }

    audit_file.write_text(json.dumps(audit_payload, ensure_ascii=False, indent=2) + "\n")
    offenders_file.write_text(json.dumps(offenders_payload, ensure_ascii=False, indent=2) + "\n")

    return audit_file, offenders_file

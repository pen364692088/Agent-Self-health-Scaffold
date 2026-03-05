#!/usr/bin/env python3

from openviking.ingest.embedding_audit import AuditChunkRecord, build_doc_audit


def test_audit_coverage_and_status_counts():
    records = [
        AuditChunkRecord(chunk_id="a", token_count=100, status="ok"),
        AuditChunkRecord(chunk_id="b", token_count=100, status="ok"),
        AuditChunkRecord(chunk_id="c", token_count=100, status="skipped"),
        AuditChunkRecord(chunk_id="d", token_count=100, status="truncated"),
    ]
    audit = build_doc_audit(
        doc_id="doc://x",
        doc_text="hello world",
        chunk_records=records,
        chunker_version="v1",
        embedding_version="e1",
    )

    assert audit["chunk_count_total"] == 4
    assert audit["chunk_count_embedded"] == 2
    assert abs(audit["embedding_coverage_pct"] - 0.5) < 1e-9
    assert audit["status_counts"]["ok"] == 2
    assert audit["status_counts"]["skipped"] == 1
    assert audit["status_counts"]["truncated"] == 1
    assert audit["max_chunk_tokens_seen"] == 100

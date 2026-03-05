#!/usr/bin/env python3
"""Generate doc-level embedding audit artifacts for OpenViking URIs.

Token counting notes:
- Prefer same-source tokenizer where available.
- Fallback token counting is approximate and may differ from provider tokenization.
- Dual guards (max_chars/max_bytes) are applied to prevent overflow regressions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from openviking.chunking.deterministic_chunker import chunk_with_stats, CHUNKER_VERSION
from openviking.ingest.embedding_audit import AuditChunkRecord, build_doc_audit, emit_audit_artifacts
from openviking.tokenization.token_counter import build_default_counter


def ov_json(args):
    p = subprocess.run(["openviking", "-o", "json", *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    return json.loads(p.stdout)


def list_docs(root_uri: str):
    payload = ov_json(["ls", root_uri])
    for item in payload.get("result", []):
        if not item.get("isDir"):
            yield item["uri"]


def read_doc(uri: str):
    payload = ov_json(["read", uri])
    return payload.get("result", "")


def _resolve_overlap(max_tokens: int, overlap_tokens: int | None) -> int:
    return overlap_tokens if overlap_tokens is not None else min(100, max_tokens // 8)


def build_parser():
    p = argparse.ArgumentParser(description="OpenViking embedding audit")
    p.add_argument("--doc-ids", nargs="*", default=[])
    p.add_argument("--root-uri", default="viking://resources/user/memory/")
    p.add_argument("--max-tokens", type=int, default=800)
    p.add_argument("--overlap-tokens", type=int, default=None)
    p.add_argument("--max-chars", type=int, default=4000)
    p.add_argument("--max-bytes", type=int, default=12000)

    p.add_argument("--tokenizer", default="auto", choices=["auto", "tiktoken", "hf", "fallback"])
    p.add_argument("--openai-model", default="text-embedding-3-large")
    p.add_argument("--hf-model")

    p.add_argument("--embedding-version", default="openviking.default")
    p.add_argument("--top-n", type=int, default=10)
    p.add_argument("--out-dir", default=str(WORKSPACE / "artifacts" / "openviking" / "audit"))
    p.add_argument("--json", action="store_true")
    p.add_argument("--health", action="store_true")
    p.add_argument("--sample", action="store_true")
    return p


def main():
    args = build_parser().parse_args()
    if args.health:
        print(json.dumps({"status": "healthy", "tool": "openviking_embedding_audit.v2"}))
        return 0
    if args.sample:
        print(json.dumps({"sample": "python scripts/openviking_embedding_audit.py --root-uri viking://resources/user/memory/"}, ensure_ascii=False))
        return 0

    counter = build_default_counter(preferred=args.tokenizer, openai_model=args.openai_model, hf_model=args.hf_model)
    doc_ids = args.doc_ids or list(list_docs(args.root_uri))
    overlap = _resolve_overlap(args.max_tokens, args.overlap_tokens)

    docs = []
    for doc_id in doc_ids:
        text = read_doc(doc_id)
        chunks, stats = chunk_with_stats(
            text,
            max_tokens=args.max_tokens,
            overlap_tokens=overlap,
            token_counter=counter,
            max_chars=args.max_chars,
            max_bytes=args.max_bytes,
        )
        records = [AuditChunkRecord(chunk_id=c.chunk_id, token_count=c.token_count, status="ok") for c in chunks]
        docs.append(
            build_doc_audit(
                doc_id=doc_id,
                doc_text=text,
                chunk_records=records,
                chunker_version=CHUNKER_VERSION,
                embedding_version=args.embedding_version,
                source="audit_only",
                token_count_method=stats.token_count_method,
                fallback_trigger_count=stats.fallback_trigger_count,
                max_chunk_chars_seen=stats.max_chunk_chars,
                max_chunk_bytes_seen=stats.max_chunk_bytes,
                dual_guard_trim_count=stats.dual_guard_trim_count,
            )
        )

    out_audit, out_offenders = emit_audit_artifacts(doc_audits=docs, out_dir=args.out_dir, top_n=args.top_n)
    payload = {
        "doc_count": len(docs),
        "audit_file": str(out_audit),
        "offenders_file": str(out_offenders),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Audit: {out_audit}\nOffenders: {out_offenders}\nDocs: {len(docs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

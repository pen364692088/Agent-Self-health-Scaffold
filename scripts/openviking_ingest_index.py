#!/usr/bin/env python3
"""OpenViking ingest/index pipeline with production artifacts and manifest."""

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
from openviking.ingest.embedding_audit import AuditChunkRecord, build_doc_audit, emit_audit_artifacts, summarize_offenders
from openviking.ingest.index_manifest import IndexManifest, ManifestRecord, now_utc_iso
from openviking.ingest.metrics import build_metrics, write_metrics
from openviking.policy.embedding_policy import load_policy, evaluate_policy
from openviking.tokenization.token_counter import build_default_counter

SCRIPT_VERSION = "openviking_ingest_index.v2"


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def ov_json(args):
    code, out, err = _run(["openviking", "-o", "json", *args])
    if code != 0:
        raise RuntimeError(err.strip())
    return json.loads(out)


def list_docs(root_uri: str):
    payload = ov_json(["ls", root_uri])
    for item in payload.get("result", []):
        if not item.get("isDir"):
            yield item["uri"]


def read_doc(uri: str):
    payload = ov_json(["read", uri])
    return payload.get("result", "")


def ingest_local(path: str, target_uri: str):
    code, out, err = _run(["openviking", "add-resource", path, "--to", target_uri, "--wait", "--timeout", "600"])
    if code != 0:
        raise RuntimeError(f"ingest failed: {err.strip()}")
    return out.strip()


def _resolve_overlap(max_tokens: int, overlap_tokens: int | None) -> int:
    return overlap_tokens if overlap_tokens is not None else min(100, max_tokens // 8)


def build_parser():
    p = argparse.ArgumentParser(description="OpenViking ingest/index with production audit outputs")
    p.add_argument("--path", help="Local file path to ingest")
    p.add_argument("--to", default="viking://resources/user/memory/", help="Target URI for ingest")
    p.add_argument("--doc-ids", nargs="*", default=[])
    p.add_argument("--root-uri", default="viking://resources/user/memory/")

    p.add_argument("--max-tokens", type=int, default=1000)
    p.add_argument("--overlap-tokens", type=int, default=None)
    p.add_argument("--max-chars", type=int, default=4000)
    p.add_argument("--max-bytes", type=int, default=12000)

    p.add_argument("--tokenizer", default="auto", choices=["auto", "tiktoken", "hf", "fallback"])
    p.add_argument("--openai-model", default="text-embedding-3-large")
    p.add_argument("--hf-model")

    p.add_argument("--embedding-version", default="openviking.default")
    p.add_argument("--policy", default=str(WORKSPACE / "config" / "openviking_embedding_policy.yaml"))
    p.add_argument("--manifest", default=str(WORKSPACE / "artifacts" / "openviking" / "index_manifest.json"))
    p.add_argument("--top-n", type=int, default=10)

    p.add_argument("--max-embed-calls", type=int)
    p.add_argument("--max-total-bytes", type=int)
    p.add_argument("--force", action="store_true")

    p.add_argument("--out-dir", default=str(WORKSPACE / "artifacts" / "openviking" / "ingest"))
    p.add_argument("--json", action="store_true")
    p.add_argument("--health", action="store_true")
    p.add_argument("--sample", action="store_true")
    return p


def main():
    args = build_parser().parse_args()

    if args.health:
        print(json.dumps({"status": "healthy", "tool": SCRIPT_VERSION}))
        return 0
    if args.sample:
        print(json.dumps({"sample": "python scripts/openviking_ingest_index.py --root-uri viking://resources/user/memory/"}, ensure_ascii=False))
        return 0

    if args.path:
        ingest_local(args.path, args.to)

    doc_ids = args.doc_ids or list(list_docs(args.root_uri))
    overlap = _resolve_overlap(args.max_tokens, args.overlap_tokens)
    counter = build_default_counter(preferred=args.tokenizer, openai_model=args.openai_model, hf_model=args.hf_model)
    policy = load_policy(args.policy)
    manifest = IndexManifest(args.manifest)

    docs = []
    decisions = []
    embed_calls_est = 0
    total_bytes_est = 0

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
        audit = build_doc_audit(
            doc_id=doc_id,
            doc_text=text,
            chunk_records=records,
            chunker_version=CHUNKER_VERSION,
            embedding_version=args.embedding_version,
            source="ingest_index",
            token_count_method=stats.token_count_method,
            fallback_trigger_count=stats.fallback_trigger_count,
            max_chunk_chars_seen=stats.max_chunk_chars,
            max_chunk_bytes_seen=stats.max_chunk_bytes,
            dual_guard_trim_count=stats.dual_guard_trim_count,
        )
        decision = evaluate_policy(audit, policy)

        docs.append(audit)
        decisions.append({"doc_id": doc_id, **decision})
        embed_calls_est += len(chunks)
        total_bytes_est += sum(len(c.text.encode("utf-8")) for c in chunks)

        manifest.upsert(
            ManifestRecord(
                doc_id=doc_id,
                doc_content_hash=audit["doc_hash"],
                chunker_version=CHUNKER_VERSION,
                embedding_version=args.embedding_version,
                embedding_complete=True,
                embedding_coverage_pct=float(audit.get("embedding_coverage_pct", 0.0)),
                indexed_at=now_utc_iso(),
            )
        )

    if not args.force:
        if args.max_embed_calls is not None and embed_calls_est > args.max_embed_calls:
            raise SystemExit(f"Cost guard: embed_calls_est {embed_calls_est} > max_embed_calls {args.max_embed_calls}")
        if args.max_total_bytes is not None and total_bytes_est > args.max_total_bytes:
            raise SystemExit(f"Cost guard: total_bytes_est {total_bytes_est} > max_total_bytes {args.max_total_bytes}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_file, offenders_file = emit_audit_artifacts(doc_audits=docs, out_dir=out_dir, top_n=args.top_n)

    policy_file = out_dir / "policy_decision.json"
    policy_file.write_text(
        json.dumps(
            {
                "generated_at": now_utc_iso(),
                "policy_mode": (policy or {}).get("mode", "warn_soft"),
                "doc_count": len(decisions),
                "decisions": decisions,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )

    offenders_top = summarize_offenders(docs, top_n=args.top_n)
    metrics = build_metrics(audits=docs, offenders_top_n=offenders_top, source="ingest_index")
    metrics_file = write_metrics(metrics, out_dir / "metrics.json")

    manifest.save()

    payload = {
        "version": SCRIPT_VERSION,
        "doc_count": len(docs),
        "cost_estimate": {
            "embed_calls_est": embed_calls_est,
            "chunk_total_est": embed_calls_est,
            "bytes_total_est": total_bytes_est,
        },
        "embedding_audit": str(audit_file),
        "embedding_offenders": str(offenders_file),
        "policy_decision": str(policy_file),
        "metrics": str(metrics_file),
        "manifest": str(manifest.path),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"Audit: {audit_file}\n"
            f"Offenders: {offenders_file}\n"
            f"Policy: {policy_file}\n"
            f"Metrics: {metrics_file}\n"
            f"Manifest: {manifest.path}\n"
            f"Docs: {len(docs)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

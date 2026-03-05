#!/usr/bin/env python3
"""Backfill embedding coverage with persistent idempotency + cost guards."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Iterable, List, Dict, Any
import sys

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from openviking.chunking.deterministic_chunker import chunk_with_stats, CHUNKER_VERSION
from openviking.ingest.embedding_audit import (
    AuditChunkRecord,
    build_doc_audit,
    emit_audit_artifacts,
    summarize_offenders,
)
from openviking.ingest.index_manifest import IndexManifest, ManifestRecord, now_utc_iso
from openviking.ingest.metrics import build_metrics, write_metrics
from openviking.policy.embedding_policy import load_policy, evaluate_policy
from openviking.tokenization.token_counter import build_default_counter

DEFAULT_URI = "viking://resources/user/memory/"
DEFAULT_OUT_DIR = WORKSPACE / "artifacts" / "openviking"
SCRIPT_VERSION = "openviking_backfill_embeddings.v3"


@dataclass
class PlanItem:
    doc_id: str
    text: str
    before: dict | None
    after: dict
    policy: dict
    chunk_count: int
    bytes_total: int
    max_chunk_tokens: int
    max_chunk_chars: int
    max_chunk_bytes: int
    token_count_method: str
    fallback_trigger_count: int
    dual_guard_trim_count: int
    idempotent_skip: bool
    skip_reason: str | None = None


def _run(cmd: List[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _ov_json(args: List[str]) -> Dict[str, Any]:
    code, out, err = _run(["openviking", "-o", "json", *args])
    if code != 0:
        raise RuntimeError(f"openviking failed: {' '.join(args)}\n{err.strip()}")
    return json.loads(out)


def _get_doc_text(doc_id: str) -> str:
    payload = _ov_json(["read", doc_id])
    if not payload.get("ok"):
        raise RuntimeError(f"failed to read doc: {doc_id}")
    result = payload.get("result", "")
    return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)


def _parse_audit(path: Path) -> Dict[str, dict]:
    data = json.loads(path.read_text())
    docs = data.get("docs", []) if isinstance(data, dict) else []
    out = {}
    for d in docs:
        doc_id = d.get("doc_id")
        if doc_id:
            out[doc_id] = d
    return out


def _collect_doc_ids(
    *,
    explicit_doc_ids: List[str],
    from_audit: Path | None,
    only_non_ok: bool,
    since_days: int | None,
    root_uri: str,
) -> tuple[List[str], Dict[str, dict]]:
    before_map: Dict[str, dict] = {}
    doc_ids = list(dict.fromkeys(explicit_doc_ids))

    if from_audit is not None and from_audit.exists():
        before_map = _parse_audit(from_audit)
        for doc_id, row in before_map.items():
            if only_non_ok and row.get("embedding_status") == "ok":
                continue
            doc_ids.append(doc_id)

    if since_days is not None and since_days > 0:
        listing = _ov_json(["ls", root_uri]).get("result", [])
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        for item in listing:
            if item.get("isDir"):
                continue
            uri = item.get("uri")
            mod = item.get("modTime", "")
            include = False
            try:
                dt = datetime.strptime(mod[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                include = dt >= cutoff
            except Exception:
                include = True
            if include and uri:
                doc_ids.append(uri)

    deduped = []
    seen = set()
    for d in doc_ids:
        if d not in seen:
            seen.add(d)
            deduped.append(d)
    return deduped, before_map


def _uri_parent(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[0] + "/" if "/" in uri.rstrip("/") else DEFAULT_URI


def _upsert_doc(doc_id: str, text: str) -> dict:
    parent_uri = _uri_parent(doc_id)
    with tempfile.TemporaryDirectory(prefix="ov_backfill_") as td:
        tmp = Path(td) / "doc.md"
        tmp.write_text(text)
        code, out, err = _run([
            "openviking",
            "add-resource",
            str(tmp),
            "--to",
            parent_uri,
            "--reason",
            "embedding_backfill",
            "--wait",
            "--timeout",
            "600",
        ])
        return {
            "ok": code == 0,
            "code": code,
            "stdout": out.strip()[:500],
            "stderr": err.strip()[:500],
            "target_uri": parent_uri,
        }


def _avg(values: Iterable[Any]) -> float:
    cleaned = [float(v) for v in values if isinstance(v, (int, float))]
    return round(sum(cleaned) / len(cleaned), 6) if cleaned else 0.0


def _resolve_overlap(max_tokens: int, overlap_tokens: int | None) -> int:
    return overlap_tokens if overlap_tokens is not None else min(100, max_tokens // 8)


def _time_estimate_sec(embed_calls_est: int, sec_per_call: float = 0.25) -> float:
    return round(embed_calls_est * sec_per_call, 3)


def _cost_guard_errors(embed_calls: int, total_bytes: int, max_embed_calls: int | None, max_total_bytes: int | None) -> list[str]:
    errs = []
    if max_embed_calls is not None and embed_calls > max_embed_calls:
        errs.append(f"embed_calls_est_exceeded:{embed_calls}>{max_embed_calls}")
    if max_total_bytes is not None and total_bytes > max_total_bytes:
        errs.append(f"bytes_total_est_exceeded:{total_bytes}>{max_total_bytes}")
    return errs


def run(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    counter = build_default_counter(preferred=args.tokenizer, openai_model=args.openai_model, hf_model=args.hf_model)
    manifest = IndexManifest(args.manifest)

    doc_ids, before_map = _collect_doc_ids(
        explicit_doc_ids=args.doc_ids or [],
        from_audit=Path(args.from_audit) if args.from_audit else None,
        only_non_ok=args.only_non_ok,
        since_days=args.since_days,
        root_uri=args.root_uri,
    )

    overlap = _resolve_overlap(args.max_tokens, args.overlap_tokens)
    out_dir = Path(args.out_dir or DEFAULT_OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    plan: list[PlanItem] = []
    failures = []

    # plan stage (no upsert yet)
    for doc_id in doc_ids:
        try:
            text = _get_doc_text(doc_id)
            doc_hash = __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()

            # persistent idempotency (manifest) regardless of --from-audit
            if args.skip_already_ok and (not args.force):
                if manifest.should_skip(
                    doc_id=doc_id,
                    doc_content_hash=doc_hash,
                    chunker_version=CHUNKER_VERSION,
                    embedding_version=args.embedding_version,
                    min_coverage=args.idempotent_min_coverage,
                ):
                    before = before_map.get(doc_id) or manifest.get(doc_id)
                    after = {
                        "doc_id": doc_id,
                        "doc_hash": doc_hash,
                        "embedding_coverage_pct": float((before or {}).get("embedding_coverage_pct", 1.0)),
                        "status_counts": {"ok": 0, "truncated": 0, "skipped": 0, "error": 0},
                        "embedding_status": "ok",
                        "chunker_version": CHUNKER_VERSION,
                        "embedding_version": args.embedding_version,
                        "token_count_method": "manifest_skip",
                        "fallback_trigger_count": 0,
                        "dual_guard_trim_count": 0,
                        "max_chunk_tokens_seen": 0,
                        "max_chunk_chars_seen": 0,
                        "max_chunk_bytes_seen": 0,
                        "indexed_at": now_utc_iso(),
                        "source": "backfill_manifest_skip",
                    }
                    decision = evaluate_policy(after, policy)
                    plan.append(
                        PlanItem(
                            doc_id=doc_id,
                            text=text,
                            before=before,
                            after=after,
                            policy=decision,
                            chunk_count=0,
                            bytes_total=0,
                            max_chunk_tokens=0,
                            max_chunk_chars=0,
                            max_chunk_bytes=0,
                            token_count_method="manifest_skip",
                            fallback_trigger_count=0,
                            dual_guard_trim_count=0,
                            idempotent_skip=True,
                            skip_reason="manifest_complete",
                        )
                    )
                    continue

            chunks, stats = chunk_with_stats(
                text,
                max_tokens=args.max_tokens,
                overlap_tokens=overlap,
                token_counter=counter,
                max_chars=args.max_chars,
                max_bytes=args.max_bytes,
            )
            records = [AuditChunkRecord(chunk_id=c.chunk_id, token_count=c.token_count, status="ok") for c in chunks]
            after = build_doc_audit(
                doc_id=doc_id,
                doc_text=text,
                chunk_records=records,
                chunker_version=CHUNKER_VERSION,
                embedding_version=args.embedding_version,
                source="backfill",
                token_count_method=stats.token_count_method,
                fallback_trigger_count=stats.fallback_trigger_count,
                max_chunk_chars_seen=stats.max_chunk_chars,
                max_chunk_bytes_seen=stats.max_chunk_bytes,
                dual_guard_trim_count=stats.dual_guard_trim_count,
            )
            decision = evaluate_policy(after, policy)

            plan.append(
                PlanItem(
                    doc_id=doc_id,
                    text=text,
                    before=before_map.get(doc_id) or manifest.get(doc_id),
                    after=after,
                    policy=decision,
                    chunk_count=len(chunks),
                    bytes_total=sum(len(c.text.encode("utf-8")) for c in chunks),
                    max_chunk_tokens=stats.max_chunk_tokens,
                    max_chunk_chars=stats.max_chunk_chars,
                    max_chunk_bytes=stats.max_chunk_bytes,
                    token_count_method=stats.token_count_method,
                    fallback_trigger_count=stats.fallback_trigger_count,
                    dual_guard_trim_count=stats.dual_guard_trim_count,
                    idempotent_skip=False,
                )
            )
        except Exception as e:
            failures.append({"doc_id": doc_id, "error": str(e)})

    embed_calls_est = sum(p.chunk_count for p in plan if not p.idempotent_skip)
    chunk_total_est = embed_calls_est
    bytes_total_est = sum(p.bytes_total for p in plan if not p.idempotent_skip)
    write_ops_est = sum(1 for p in plan if not p.idempotent_skip) if args.upsert and not args.dry_run else 0
    time_est = _time_estimate_sec(embed_calls_est, sec_per_call=args.sec_per_embed_call)

    guard_errors = _cost_guard_errors(
        embed_calls=embed_calls_est,
        total_bytes=bytes_total_est,
        max_embed_calls=args.max_embed_calls,
        max_total_bytes=args.max_total_bytes,
    )

    if guard_errors and not args.force:
        error_payload = {
            "version": SCRIPT_VERSION,
            "status": "cost_guard_blocked",
            "errors": guard_errors,
            "cost_estimate": {
                "embed_calls_est": embed_calls_est,
                "chunk_total_est": chunk_total_est,
                "bytes_total_est": bytes_total_est,
                "time_est_sec": time_est,
            },
            "suggestions": [
                "Reduce scope via --doc-ids or --since-days",
                "Lower max_tokens or max_chars/max_bytes",
                "Run with --dry-run first, or use --force to override guard",
            ],
        }
        (out_dir / "cost_guard_error.json").write_text(json.dumps(error_payload, ensure_ascii=False, indent=2) + "\n")
        if args.json:
            print(json.dumps(error_payload, ensure_ascii=False, indent=2))
        else:
            print("Cost guard blocked execution")
            print(json.dumps(error_payload, ensure_ascii=False, indent=2))
        return 2

    # execute upserts after guard pass
    for p in plan:
        if p.idempotent_skip:
            continue
        if args.upsert and not args.dry_run:
            up = _upsert_doc(p.doc_id, p.text)
            if up.get("ok"):
                manifest.upsert(
                    ManifestRecord(
                        doc_id=p.doc_id,
                        doc_content_hash=p.after["doc_hash"],
                        chunker_version=CHUNKER_VERSION,
                        embedding_version=args.embedding_version,
                        embedding_complete=True,
                        embedding_coverage_pct=float(p.after.get("embedding_coverage_pct", 0.0)),
                        indexed_at=now_utc_iso(),
                    )
                )

    manifest.save()

    audits = [p.after for p in plan]
    audit_path, offenders_path = emit_audit_artifacts(doc_audits=audits, out_dir=out_dir, top_n=args.top_n)
    offenders_top = summarize_offenders(audits, top_n=args.top_n)

    # policy decision artifact
    policy_path = out_dir / "policy_decision.json"
    policy_payload = {
        "generated_at": now_utc_iso(),
        "policy_mode": (policy or {}).get("mode", "warn_soft"),
        "doc_count": len(plan),
        "decisions": [{"doc_id": p.doc_id, **p.policy} for p in plan],
    }
    policy_path.write_text(json.dumps(policy_payload, ensure_ascii=False, indent=2) + "\n")

    # metrics artifact
    metrics = build_metrics(audits=audits, offenders_top_n=offenders_top, source="backfill")
    metrics_path = write_metrics(metrics, out_dir / "metrics.json")

    report_rows = []
    for p in plan:
        report_rows.append(
            {
                "doc_id": p.doc_id,
                "before": p.before,
                "after": p.after,
                "policy": p.policy,
                "chunk_count": p.chunk_count,
                "max_chunk_tokens": p.max_chunk_tokens,
                "max_chunk_chars": p.max_chunk_chars,
                "max_chunk_bytes": p.max_chunk_bytes,
                "token_count_method": p.token_count_method,
                "fallback_trigger_count": p.fallback_trigger_count,
                "dual_guard_trim_count": p.dual_guard_trim_count,
                "idempotent_skip": p.idempotent_skip,
                "explain": {
                    "skip_reason": p.skip_reason,
                    "dual_guard_triggered": p.dual_guard_trim_count > 0,
                    "fallback_triggered": p.fallback_trigger_count > 0,
                },
            }
        )

    report = {
        "version": SCRIPT_VERSION,
        "generated_at": now_utc_iso(),
        "dry_run": args.dry_run,
        "upsert": args.upsert,
        "inputs": {
            "doc_ids_count": len(doc_ids),
            "from_audit": args.from_audit,
            "since_days": args.since_days,
            "only_non_ok": args.only_non_ok,
            "root_uri": args.root_uri,
        },
        "params": {
            "max_tokens": args.max_tokens,
            "overlap_tokens": overlap,
            "overlap_policy": "min(100,max_tokens//8)" if args.overlap_tokens is None else "fixed",
            "max_chars": args.max_chars,
            "max_bytes": args.max_bytes,
            "embedding_version": args.embedding_version,
            "policy": args.policy,
            "tokenizer": args.tokenizer,
            "openai_model": args.openai_model,
            "hf_model": args.hf_model,
            "manifest": args.manifest,
        },
        "cost_estimate": {
            "embed_calls_est": embed_calls_est,
            "chunk_total_est": chunk_total_est,
            "bytes_total_est": bytes_total_est,
            "time_est_sec": time_est,
            "write_ops_est": write_ops_est,
        },
        "summary": {
            "processed": len(report_rows),
            "failed": len(failures),
            "coverage_before_avg": _avg([(r.get("before") or {}).get("embedding_coverage_pct") for r in report_rows]),
            "coverage_after_avg": _avg([r.get("after", {}).get("embedding_coverage_pct") for r in report_rows]),
            "skipped_after_total": sum((r.get("after") or {}).get("status_counts", {}).get("skipped", 0) for r in report_rows),
            "idempotent_skipped": sum(1 for r in report_rows if r.get("idempotent_skip")),
        },
        "artifacts": {
            "embedding_audit": str(audit_path),
            "offenders": str(offenders_path),
            "policy_decision": str(policy_path),
            "metrics": str(metrics_path),
            "manifest": str(manifest.path),
        },
        "results": report_rows,
        "failures": failures,
    }

    out_file = out_dir / "backfill_report.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Backfill report: {out_file}")
        print(f"Processed: {report['summary']['processed']}, Failed: {report['summary']['failed']}")
        print(f"Coverage avg before -> after: {report['summary']['coverage_before_avg']} -> {report['summary']['coverage_after_avg']}")

    return 0 if not failures else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OpenViking embedding backfill tool")
    p.add_argument("--doc-ids", nargs="*", default=[], help="OpenViking URIs")
    p.add_argument("--from-audit", help="Path to embedding_audit.json")
    p.add_argument("--since-days", type=int, help="Include docs updated in last N days")
    p.add_argument("--root-uri", default=DEFAULT_URI, help="Root URI for --since-days scan")
    p.add_argument("--only-non-ok", action="store_true", help="From audit: only docs with status != ok")

    p.add_argument("--max-tokens", type=int, default=800)
    p.add_argument("--overlap-tokens", type=int, default=None)
    p.add_argument("--max-chars", type=int, default=4000)
    p.add_argument("--max-bytes", type=int, default=12000)

    p.add_argument("--tokenizer", default="auto", choices=["auto", "tiktoken", "hf", "fallback"])
    p.add_argument("--openai-model", default="text-embedding-3-large")
    p.add_argument("--hf-model")

    p.add_argument("--embedding-version", default="openviking.default")
    p.add_argument("--policy", default=str(WORKSPACE / "config" / "openviking_embedding_policy.yaml"))
    p.add_argument("--manifest", default=str(WORKSPACE / "artifacts" / "openviking" / "index_manifest.json"))

    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--upsert", action="store_true")
    p.add_argument("--skip-already-ok", action="store_true", default=True)
    p.add_argument("--idempotent-min-coverage", type=float, default=0.98)
    p.add_argument("--force", action="store_true")
    p.add_argument("--top-n", type=int, default=10)

    p.add_argument("--max-embed-calls", type=int)
    p.add_argument("--max-total-bytes", type=int)
    p.add_argument("--sec-per-embed-call", type=float, default=0.25)

    p.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    p.add_argument("--json", action="store_true")

    p.add_argument("--health", action="store_true", help="Health probe")
    p.add_argument("--sample", action="store_true", help="Sample probe")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.health:
        print(json.dumps({"status": "healthy", "tool": SCRIPT_VERSION}))
        return 0

    if args.sample:
        sample = {
            "tool": SCRIPT_VERSION,
            "sample_command": "python scripts/openviking_backfill_embeddings.py --doc-ids <uri> --dry-run --json",
            "notes": "Persistent idempotency manifest + cost guard + metrics + policy artifacts",
        }
        print(json.dumps(sample, ensure_ascii=False, indent=2))
        return 0

    if not (args.doc_ids or args.from_audit or args.since_days):
        parser.error("Provide at least one source: --doc-ids or --from-audit or --since-days")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())

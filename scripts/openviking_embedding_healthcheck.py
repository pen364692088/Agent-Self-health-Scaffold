#!/usr/bin/env python3
"""Single-command runtime health check for embedding pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCRIPT_VERSION = "openviking_embedding_healthcheck.v1"


def build_parser():
    p = argparse.ArgumentParser(description="OpenViking embedding health check")
    p.add_argument("--metrics", required=False, help="Path to metrics.json")
    p.add_argument("--policy", required=False, help="Path to policy_decision.json")
    p.add_argument("--min-coverage", type=float, default=0.90)
    p.add_argument("--max-skipped", type=int, default=0)
    p.add_argument("--json", action="store_true")
    p.add_argument("--health", action="store_true")
    p.add_argument("--sample", action="store_true")
    return p


def _load(p: str | None):
    if not p:
        return {}
    path = Path(p)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def main() -> int:
    args = build_parser().parse_args()

    if args.health:
        print(json.dumps({"status": "healthy", "tool": SCRIPT_VERSION}))
        return 0

    if args.sample:
        print(json.dumps({"sample": "python scripts/openviking_embedding_healthcheck.py --metrics artifacts/.../metrics.json --policy artifacts/.../policy_decision.json"}, ensure_ascii=False))
        return 0

    metrics = _load(args.metrics)
    policy = _load(args.policy)

    coverage_min = float(metrics.get("coverage", {}).get("min", 1.0))
    skipped = int(metrics.get("skipped_chunks_count", 0))

    levels = [d.get("level", "OK") for d in policy.get("decisions", [])] if policy else []
    has_error = any(l == "ERROR" for l in levels)
    has_warn = any(l == "WARN" for l in levels)

    reasons = []
    exit_code = 0
    status = "HEALTHY"

    if coverage_min < args.min_coverage or skipped > args.max_skipped or has_error:
        status = "ALERT"
        exit_code = 2
        if coverage_min < args.min_coverage:
            reasons.append(f"coverage_min_below_threshold:{coverage_min}<{args.min_coverage}")
        if skipped > args.max_skipped:
            reasons.append(f"skipped_chunks_exceeded:{skipped}>{args.max_skipped}")
        if has_error:
            reasons.append("policy_error_present")
    elif has_warn:
        status = "WARN"
        exit_code = 1
        reasons.append("policy_warn_present")

    payload = {
        "version": SCRIPT_VERSION,
        "status": status,
        "coverage_min": coverage_min,
        "skipped_chunks_count": skipped,
        "policy_levels": {"error": has_error, "warn": has_warn},
        "reasons": reasons,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

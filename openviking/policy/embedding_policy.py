#!/usr/bin/env python3
"""Policy gate for embedding coverage alerts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

DEFAULT_POLICY = {
    "mode": "warn_soft",
    "thresholds": {
        "min_coverage_pct": 0.90,
        "max_skipped_chunks": 0,
    },
    "severity": {
        "warn_soft": "WARN_SOFT",
        "warn": "WARN",
        "error": "ERROR",
    },
}


def _simple_yaml_load(path: Path) -> Dict[str, Any]:
    """Tiny yaml reader for this config shape only."""
    data: Dict[str, Any] = {}
    current = data
    stack = [(0, data)]

    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        line = line.strip()
        if ":" not in line:
            continue
        key, value = [x.strip() for x in line.split(":", 1)]

        while stack and indent < stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else data

        if value == "":
            node: Dict[str, Any] = {}
            parent[key] = node
            stack.append((indent + 2, node))
            continue

        # scalar coercion
        if value.lower() in {"true", "false"}:
            coerced: Any = value.lower() == "true"
        else:
            try:
                coerced = float(value) if "." in value else int(value)
            except ValueError:
                coerced = value.strip('"').strip("'")
        parent[key] = coerced

    return data


def load_policy(path: str | Path | None = None) -> Dict[str, Any]:
    if path is None:
        return DEFAULT_POLICY

    p = Path(path)
    if not p.exists():
        return DEFAULT_POLICY

    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(p.read_text())
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass

    parsed = _simple_yaml_load(p)
    if isinstance(parsed, dict) and parsed:
        return parsed
    return DEFAULT_POLICY


def evaluate_policy(audit: Dict[str, Any], policy: Dict[str, Any] | None = None) -> Dict[str, Any]:
    p = policy or DEFAULT_POLICY
    thresholds = p.get("thresholds", {})

    min_cov = float(thresholds.get("min_coverage_pct", 0.90))
    max_skipped = int(thresholds.get("max_skipped_chunks", 0))

    coverage = float(audit.get("embedding_coverage_pct", 0.0))
    skipped = int(audit.get("status_counts", {}).get("skipped", 0))

    reasons = []
    if coverage < min_cov:
        reasons.append(f"coverage_below_threshold:{coverage:.3f}<{min_cov:.3f}")
    if skipped > max_skipped:
        reasons.append(f"skipped_chunks_exceeded:{skipped}>{max_skipped}")

    mode = str(p.get("mode", "warn_soft")).lower()
    severity_map = p.get("severity", DEFAULT_POLICY["severity"])

    if not reasons:
        level = "OK"
    else:
        level = severity_map.get(mode, "WARN_SOFT")

    suggestions = []
    if reasons:
        doc_id = audit.get("doc_id", "<doc_id>")
        suggestions = [
            "Run deterministic rechunk + re-embed backfill",
            f"python scripts/openviking_backfill_embeddings.py --doc-ids {doc_id} --upsert",
            "Reduce max_tokens or increase split strictness if offenders persist",
        ]

    return {
        "level": level,
        "reasons": reasons,
        "suggested_actions": suggestions,
        "policy_mode": mode,
    }

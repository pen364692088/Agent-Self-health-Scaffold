#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

WORKSPACE = Path("/home/moonlight/.openclaw/workspace")
SCRIPT = WORKSPACE / "scripts" / "openviking_backfill_embeddings.py"


def _pick_one_doc_uri() -> str:
    result = subprocess.run(
        ["openviking", "-o", "json", "ls", "viking://resources/user/memory/"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    for item in payload.get("result", []):
        if not item.get("isDir"):
            return item["uri"]
    raise RuntimeError("No leaf doc found")


def test_backfill_idempotent_skip_without_audit_by_manifest(tmp_path):
    uri = _pick_one_doc_uri()
    manifest = tmp_path / "index_manifest.json"

    out1 = tmp_path / "first"
    out2 = tmp_path / "second"

    # First run writes manifest (upsert mode)
    cmd1 = [
        "python3",
        str(SCRIPT),
        "--doc-ids",
        uri,
        "--upsert",
        "--manifest",
        str(manifest),
        "--out-dir",
        str(out1),
        "--json",
    ]
    r1 = subprocess.run(cmd1, capture_output=True, text=True)
    assert r1.returncode == 0, r1.stderr

    # Second run: no --from-audit, should skip via persistent manifest
    cmd2 = [
        "python3",
        str(SCRIPT),
        "--doc-ids",
        uri,
        "--upsert",
        "--manifest",
        str(manifest),
        "--out-dir",
        str(out2),
        "--json",
    ]
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    assert r2.returncode == 0, r2.stderr

    payload = json.loads(r2.stdout)
    assert payload["summary"]["idempotent_skipped"] >= 1
    assert payload["cost_estimate"]["write_ops_est"] == 0
    assert payload["cost_estimate"]["embed_calls_est"] == 0

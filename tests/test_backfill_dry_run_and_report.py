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
    raise RuntimeError("No leaf doc found under memory URI")


def test_backfill_dry_run_generates_report(tmp_path):
    uri = _pick_one_doc_uri()
    out_dir = tmp_path / "ov"

    cmd = [
        "python3",
        str(SCRIPT),
        "--doc-ids",
        uri,
        "--dry-run",
        "--out-dir",
        str(out_dir),
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

    report_file = out_dir / "backfill_report.json"
    assert report_file.exists(), "backfill_report.json not created"

    report = json.loads(report_file.read_text())
    assert report["summary"]["processed"] >= 1
    assert "embedding_audit" in report["artifacts"]
    assert "offenders" in report["artifacts"]

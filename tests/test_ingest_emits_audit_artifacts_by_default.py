#!/usr/bin/env python3
import os

import json
import subprocess
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).parent.parent))
SCRIPT = WORKSPACE / "scripts" / "openviking_ingest_index.py"


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


def test_ingest_emits_audit_artifacts_by_default(tmp_path):
    uri = _pick_one_doc_uri()
    out_dir = tmp_path / "ingest"
    cmd = [
        "python3",
        str(SCRIPT),
        "--doc-ids",
        uri,
        "--out-dir",
        str(out_dir),
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert Path(payload["embedding_audit"]).exists()
    assert Path(payload["embedding_offenders"]).exists()
    assert Path(payload["policy_decision"]).exists()

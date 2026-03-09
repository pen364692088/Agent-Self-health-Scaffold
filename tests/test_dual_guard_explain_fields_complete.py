#!/usr/bin/env python3
import os

import json
import subprocess
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", Path(__file__).parent.parent))
SCRIPT = WORKSPACE / "scripts" / "openviking_backfill_embeddings.py"


def _prepare_long_doc(tmp_path: Path) -> str:
    p = tmp_path / "long_doc.md"
    p.write_text("# T\n\n" + ("无空格长字符串ABC123" * 10000))
    r = subprocess.run(
        [
            "openviking",
            "add-resource",
            str(p),
            "--to",
            "viking://resources/user/memory/test-dual-guard/",
            "--wait",
            "--timeout",
            "120",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    root_uri = payload["result"]["root_uri"]

    # find one leaf doc with real content
    ls = subprocess.run(["openviking", "-o", "json", "ls", root_uri + "/T"], capture_output=True, text=True)
    assert ls.returncode == 0, ls.stderr
    data = json.loads(ls.stdout)
    for item in data.get("result", []):
        if not item.get("isDir"):
            return item["uri"]
    raise RuntimeError("No leaf doc found in prepared long doc")


def test_dual_guard_explain_fields_complete(tmp_path):
    uri = _prepare_long_doc(tmp_path)
    out_dir = tmp_path / "out"

    cmd = [
        "python3",
        str(SCRIPT),
        "--doc-ids",
        uri,
        "--dry-run",
        "--max-tokens",
        "9999",
        "--max-chars",
        "80",
        "--max-bytes",
        "240",
        "--out-dir",
        str(out_dir),
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    row = payload["results"][0]

    assert "explain" in row
    assert set(["skip_reason", "dual_guard_triggered", "fallback_triggered"]).issubset(row["explain"].keys())
    assert row["dual_guard_trim_count"] >= 0

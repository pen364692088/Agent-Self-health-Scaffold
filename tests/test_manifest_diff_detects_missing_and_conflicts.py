#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
DIFF = WORKSPACE / 'scripts' / 'openviking_manifest_diff.py'


def test_manifest_diff_detects_missing_and_conflicts(tmp_path):
    left = tmp_path / 'left.json'
    right = tmp_path / 'right.json'

    left.write_text(json.dumps({'version': 'index_manifest.v1', 'docs': {
        'doc://a': {'doc_content_hash': 'h1', 'chunker_version': 'v2', 'embedding_version': 'e1'},
        'doc://b': {'doc_content_hash': 'h2', 'chunker_version': 'v2', 'embedding_version': 'e1'},
    }}))
    right.write_text(json.dumps({'version': 'index_manifest.v1', 'docs': {
        'doc://a': {'doc_content_hash': 'DIFF', 'chunker_version': 'v2', 'embedding_version': 'e1'},
        'doc://c': {'doc_content_hash': 'h3', 'chunker_version': 'v2', 'embedding_version': 'e1'},
    }}))

    r = subprocess.run(['python3', str(DIFF), '--left', str(left), '--right', str(right), '--json'], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)

    assert 'doc://b' in payload['missing_in_right']
    assert 'doc://c' in payload['extra_in_right']
    assert any(c['doc_id'] == 'doc://a' for c in payload['conflicts'])

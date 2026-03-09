#!/usr/bin/env python3
import os

import json
import subprocess
from pathlib import Path

WORKSPACE = Path(os.environ.get('OPENCLAW_WORKSPACE', Path(__file__).parent.parent))
EXPORT = WORKSPACE / 'scripts' / 'openviking_manifest_export.py'
IMPORT = WORKSPACE / 'scripts' / 'openviking_manifest_import.py'


def test_manifest_export_import_roundtrip(tmp_path):
    src_manifest = tmp_path / 'src_manifest.json'
    src_manifest.write_text(json.dumps({
        'version': 'index_manifest.v1',
        'docs': {
            'doc://1': {
                'doc_id': 'doc://1',
                'doc_content_hash': 'aaa',
                'chunker_version': 'v2',
                'embedding_version': 'e1',
                'embedding_complete': True,
                'embedding_coverage_pct': 1.0,
                'indexed_at': 'now',
            }
        }
    }))

    exported = tmp_path / 'manifest_export.json'
    target_manifest = tmp_path / 'target_manifest.json'

    r1 = subprocess.run(['python3', str(EXPORT), '--manifest', str(src_manifest), '--out', str(exported)], capture_output=True, text=True)
    assert r1.returncode == 0, r1.stderr

    r2 = subprocess.run(['python3', str(IMPORT), '--in', str(exported), '--manifest', str(target_manifest), '--replace'], capture_output=True, text=True)
    assert r2.returncode == 0, r2.stderr

    src = json.loads(src_manifest.read_text())
    tgt = json.loads(target_manifest.read_text())
    assert src['docs'].keys() == tgt['docs'].keys()
    assert tgt['docs']['doc://1']['doc_content_hash'] == 'aaa'

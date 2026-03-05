#!/usr/bin/env python3
"""Export manifest sidecar with checksum and metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCRIPT_VERSION = 'openviking_manifest_export.v1'


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Export OpenViking manifest')
    p.add_argument('--manifest', default='/home/moonlight/.openclaw/workspace/artifacts/openviking/index_manifest.json')
    p.add_argument('--out')
    p.add_argument('--json', action='store_true')
    p.add_argument('--health', action='store_true')
    p.add_argument('--sample', action='store_true')
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.health:
        print(json.dumps({'status': 'healthy', 'tool': SCRIPT_VERSION}))
        return 0
    if args.sample:
        print(json.dumps({'sample': 'python scripts/openviking_manifest_export.py --out artifacts/openviking/manifest_export.json'}))
        return 0

    if not args.out:
        raise SystemExit('--out is required unless --health/--sample is used')

    m = Path(args.manifest)
    data = json.loads(m.read_text()) if m.exists() else {'version': 'index_manifest.v1', 'docs': {}}
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode('utf-8')

    payload = {
        'version': 'manifest_export.v1',
        'script_version': SCRIPT_VERSION,
        'source_manifest': str(m),
        'source_checksum': sha256_bytes(raw),
        'doc_count': len(data.get('docs', {})),
        'manifest': data,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')

    if args.json:
        print(json.dumps({'out': str(out), 'doc_count': payload['doc_count']}, ensure_ascii=False, indent=2))
    else:
        print(f'Exported: {out} docs={payload["doc_count"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

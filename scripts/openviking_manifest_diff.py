#!/usr/bin/env python3
"""Diff two manifest files and report missing/extra/conflicts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCRIPT_VERSION = 'openviking_manifest_diff.v1'


def _docs(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if 'manifest' in data:
        data = data['manifest']
    return data.get('docs', {}) if isinstance(data, dict) else {}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Diff OpenViking manifests')
    p.add_argument('--left')
    p.add_argument('--right')
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
        print(json.dumps({'sample': 'python scripts/openviking_manifest_diff.py --left a.json --right b.json'}))
        return 0

    if not args.left or not args.right:
        raise SystemExit('--left and --right are required unless --health/--sample is used')

    left = _docs(Path(args.left))
    right = _docs(Path(args.right))

    left_keys = set(left.keys())
    right_keys = set(right.keys())

    missing_in_right = sorted(left_keys - right_keys)
    extra_in_right = sorted(right_keys - left_keys)

    conflicts = []
    for k in sorted(left_keys & right_keys):
        l = left.get(k, {})
        r = right.get(k, {})
        if (
            l.get('doc_content_hash') != r.get('doc_content_hash')
            or l.get('chunker_version') != r.get('chunker_version')
            or l.get('embedding_version') != r.get('embedding_version')
        ):
            conflicts.append({
                'doc_id': k,
                'left': {
                    'doc_content_hash': l.get('doc_content_hash'),
                    'chunker_version': l.get('chunker_version'),
                    'embedding_version': l.get('embedding_version'),
                },
                'right': {
                    'doc_content_hash': r.get('doc_content_hash'),
                    'chunker_version': r.get('chunker_version'),
                    'embedding_version': r.get('embedding_version'),
                },
            })

    payload = {
        'version': 'manifest_diff.v1',
        'left_count': len(left),
        'right_count': len(right),
        'missing_in_right': missing_in_right,
        'extra_in_right': extra_in_right,
        'conflicts': conflicts,
    }

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

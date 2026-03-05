#!/usr/bin/env python3
"""Import manifest export into target sidecar with merge/replace."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCRIPT_VERSION = 'openviking_manifest_import.v1'


def _hash_manifest(manifest: dict) -> str:
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Import OpenViking manifest export')
    p.add_argument('--in', dest='inp')
    p.add_argument('--manifest', default='/home/moonlight/.openclaw/workspace/artifacts/openviking/index_manifest.json')
    mode = p.add_mutually_exclusive_group(required=False)
    mode.add_argument('--merge', action='store_true')
    mode.add_argument('--replace', action='store_true')
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
        print(json.dumps({'sample': 'python scripts/openviking_manifest_import.py --in artifacts/openviking/manifest_export.json --merge'}))
        return 0

    if not args.inp:
        raise SystemExit('--in is required unless --health/--sample is used')

    inp = Path(args.inp)
    exp = json.loads(inp.read_text())
    imp_manifest = exp.get('manifest', {'version': 'index_manifest.v1', 'docs': {}})

    src_hash = _hash_manifest(imp_manifest)
    if exp.get('source_checksum') and exp['source_checksum'] != src_hash:
        raise SystemExit('checksum mismatch in import payload')

    target = Path(args.manifest)
    target_data = json.loads(target.read_text()) if target.exists() else {'version': 'index_manifest.v1', 'docs': {}}

    if args.replace:
        out_data = imp_manifest
        mode = 'replace'
    else:
        mode = 'merge'
        out_data = {'version': 'index_manifest.v1', 'docs': {}}
        out_data['docs'].update(target_data.get('docs', {}))
        out_data['docs'].update(imp_manifest.get('docs', {}))

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out_data, ensure_ascii=False, indent=2) + '\n')

    payload = {
        'mode': mode,
        'target_manifest': str(target),
        'doc_count': len(out_data.get('docs', {})),
        'source_doc_count': len(imp_manifest.get('docs', {})),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

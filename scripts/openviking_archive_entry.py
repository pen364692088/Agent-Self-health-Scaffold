#!/usr/bin/env python3
"""Archive entrypoint: ingest distilled files via hardened OpenViking pipeline.

This script is the default archival entry:
- ingest file(s) into target URI
- discover leaf docs under returned root_uri
- run deterministic backfill pipeline (idempotent + cost guard + metrics)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
BACKFILL = WORKSPACE / 'scripts' / 'openviking_backfill_embeddings.py'
SCRIPT_VERSION = 'openviking_archive_entry.v1'


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _json_cmd(cmd: list[str]) -> dict:
    code, out, err = _run(cmd)
    if code != 0:
        raise RuntimeError(f"command failed ({code}): {' '.join(cmd)}\n{err.strip()}")
    try:
        return json.loads(out)
    except Exception as e:
        raise RuntimeError(f"invalid JSON output: {e}\n{out[:300]}")


def _add_resource(path: Path, to_uri: str, timeout: int) -> dict:
    return _json_cmd([
        'openviking',
        'add-resource',
        str(path),
        '--to',
        to_uri,
        '--wait',
        '--timeout',
        str(timeout),
    ])


def _list_leaves(root_uri: str) -> list[str]:
    leaves: list[str] = []
    queue = [root_uri]
    seen = set()

    while queue:
        uri = queue.pop(0)
        if uri in seen:
            continue
        seen.add(uri)

        data = _json_cmd(['openviking', '-o', 'json', 'ls', uri])
        for item in data.get('result', []):
            u = item.get('uri')
            if not u:
                continue
            if item.get('isDir'):
                queue.append(u)
            else:
                leaves.append(u)

    return sorted(set(leaves))


def _backfill(leaves: list[str], out_dir: Path, *, max_tokens: int, overlap_tokens: int | None, max_chars: int, max_bytes: int, tokenizer: str, openai_model: str, hf_model: str | None, embedding_version: str, dry_run: bool) -> dict:
    cmd = [
        'python3',
        str(BACKFILL),
        '--doc-ids',
        *leaves,
        '--out-dir',
        str(out_dir),
        '--max-tokens',
        str(max_tokens),
        '--max-chars',
        str(max_chars),
        '--max-bytes',
        str(max_bytes),
        '--tokenizer',
        tokenizer,
        '--openai-model',
        openai_model,
        '--embedding-version',
        embedding_version,
        '--upsert',
        '--json',
    ]
    if overlap_tokens is not None:
        cmd.extend(['--overlap-tokens', str(overlap_tokens)])
    if hf_model:
        cmd.extend(['--hf-model', hf_model])
    if dry_run:
        cmd.append('--dry-run')

    return _json_cmd(cmd)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='OpenViking archive entrypoint (hardened pipeline)')
    p.add_argument('--daily-log', help='Path to memory/YYYY-MM-DD.md')
    p.add_argument('--memory-file', default=str(WORKSPACE / 'memory.md'), help='Path to memory.md')
    p.add_argument('--include-memory-file', action='store_true', default=True, help='Include memory.md in archive pipeline')
    p.add_argument('--exclude-memory-file', action='store_true', help='Skip memory.md indexing')

    p.add_argument('--sessions-uri', default='viking://resources/user/sessions/daily/', help='Target URI for daily log')
    p.add_argument('--memory-uri', default='viking://resources/user/memory/', help='Target URI for long-term memory file')

    p.add_argument('--max-tokens', type=int, default=800)
    p.add_argument('--overlap-tokens', type=int, default=None)
    p.add_argument('--max-chars', type=int, default=4000)
    p.add_argument('--max-bytes', type=int, default=12000)
    p.add_argument('--tokenizer', default='auto', choices=['auto', 'tiktoken', 'hf', 'fallback'])
    p.add_argument('--openai-model', default='text-embedding-3-large')
    p.add_argument('--hf-model')
    p.add_argument('--embedding-version', default='openviking.default')

    p.add_argument('--timeout', type=int, default=120)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--out-dir', default=str(WORKSPACE / 'artifacts' / 'openviking' / 'archive'))
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
        print(json.dumps({'sample': 'python scripts/openviking_archive_entry.py --daily-log memory/2026-03-04.md --include-memory-file --json'}, ensure_ascii=False))
        return 0

    if not args.daily_log:
        raise SystemExit('--daily-log is required unless --health/--sample is used')

    include_memory = bool(args.include_memory_file and not args.exclude_memory_file)
    daily_log = Path(args.daily_log)
    memory_file = Path(args.memory_file)

    if not daily_log.exists():
        raise SystemExit(f'daily log not found: {daily_log}')
    if include_memory and not memory_file.exists():
        include_memory = False

    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out_root = Path(args.out_dir) / ts
    out_root.mkdir(parents=True, exist_ok=True)

    targets = [
        {'name': 'daily_log', 'path': daily_log, 'uri': args.sessions_uri},
    ]
    if include_memory:
        targets.append({'name': 'memory_file', 'path': memory_file, 'uri': args.memory_uri})

    results = []
    failures = []

    for t in targets:
        name = t['name']
        path = t['path']
        uri = t['uri']
        try:
            add_res = _add_resource(path, uri, timeout=args.timeout)
            root_uri = add_res.get('result', {}).get('root_uri')
            if not root_uri:
                raise RuntimeError(f'missing root_uri from add-resource for {path}')

            leaves = _list_leaves(root_uri)
            if not leaves:
                raise RuntimeError(f'no leaf docs discovered under root_uri: {root_uri}')

            bf_out = out_root / name
            bf_res = _backfill(
                leaves,
                bf_out,
                max_tokens=args.max_tokens,
                overlap_tokens=args.overlap_tokens,
                max_chars=args.max_chars,
                max_bytes=args.max_bytes,
                tokenizer=args.tokenizer,
                openai_model=args.openai_model,
                hf_model=args.hf_model,
                embedding_version=args.embedding_version,
                dry_run=args.dry_run,
            )

            results.append({
                'name': name,
                'source_file': str(path),
                'target_uri': uri,
                'root_uri': root_uri,
                'leaf_count': len(leaves),
                'backfill_out_dir': str(bf_out),
                'summary': bf_res.get('summary', {}),
                'cost_estimate': bf_res.get('cost_estimate', {}),
                'artifacts': bf_res.get('artifacts', {}),
            })
        except Exception as e:
            failures.append({'name': name, 'source_file': str(path), 'error': str(e)})

    payload = {
        'version': SCRIPT_VERSION,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'dry_run': args.dry_run,
        'results': results,
        'failures': failures,
        'out_root': str(out_root),
    }

    (out_root / 'archive_entry_report.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Archive entry done: {out_root} (results={len(results)}, failures={len(failures)})")

    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())

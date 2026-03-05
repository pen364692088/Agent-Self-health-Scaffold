#!/usr/bin/env python3
"""Retention cleanup for ops artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
SCRIPT_VERSION = 'openviking_ops_retention_gc.v1'


def _load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
        d = yaml.safe_load(path.read_text())
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _days_old(path: Path) -> float:
    dt = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0


def _gc_dir(root: Path, keep_days: int) -> tuple[int, int]:
    if not root.exists():
        return (0, 0)
    removed = 0
    scanned = 0
    for p in sorted(root.glob('*')):
        scanned += 1
        if _days_old(p) > keep_days:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
            removed += 1
    return scanned, removed


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='OpenViking retention gc')
    p.add_argument('--config', default=str(WORKSPACE / 'config' / 'openviking_ops.yaml'))
    p.add_argument('--ops-runs-days', type=int)
    p.add_argument('--daily-days', type=int)
    p.add_argument('--alerts-days', type=int)
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
        print(json.dumps({'sample': 'python scripts/openviking_ops_retention_gc.py'}))
        return 0

    cfg = _load_yaml(Path(args.config)) if Path(args.config).exists() else {}
    ret = cfg.get('retention', {}) if isinstance(cfg.get('retention', {}), dict) else {}

    ops_days = args.ops_runs_days if args.ops_runs_days is not None else int(ret.get('ops_runs_days', 14))
    daily_days = args.daily_days if args.daily_days is not None else int(ret.get('daily_days', 30))
    alerts_days = args.alerts_days if args.alerts_days is not None else int(ret.get('alerts_days', 30))

    roots = {
        'ops_runs': (WORKSPACE / 'artifacts' / 'openviking' / 'ops_runs', ops_days),
        'daily': (WORKSPACE / 'artifacts' / 'openviking' / 'daily', daily_days),
        'alerts_failed': (WORKSPACE / 'artifacts' / 'openviking' / 'alerts' / 'failed', alerts_days),
    }

    summary = {'version': SCRIPT_VERSION, 'at': datetime.now(timezone.utc).isoformat(), 'results': {}}
    for name, (root, days) in roots.items():
        scanned, removed = _gc_dir(root, days)
        summary['results'][name] = {'root': str(root), 'keep_days': days, 'scanned': scanned, 'removed': removed}

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Daily rollup for OpenViking ops runs."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import statistics

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
SCRIPT_VERSION = 'openviking_daily_rollup.v1'


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _pick_date(date_str: str | None) -> str:
    if date_str in {None, '', 'today'}:
        return datetime.now(timezone.utc).strftime('%Y%m%d')
    if date_str == 'yesterday':
        return (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y%m%d')
    # accept YYYYMMDD or YYYY-MM-DD
    if '-' in date_str:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y%m%d')
    return date_str


def _p(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    idx = (len(vals) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(vals) - 1)
    frac = idx - lo
    return round(vals[lo] * (1 - frac) + vals[hi] * frac, 6)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='OpenViking daily rollup')
    p.add_argument('--date', default='today')
    p.add_argument('--ops-root', default=str(WORKSPACE / 'artifacts' / 'openviking' / 'ops_runs'))
    p.add_argument('--out-root', default=str(WORKSPACE / 'artifacts' / 'openviking' / 'daily'))
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
        print(json.dumps({'sample': 'python scripts/openviking_daily_rollup.py --date today'}, ensure_ascii=False))
        return 0

    day = _pick_date(args.date)
    ops_day = Path(args.ops_root) / day
    out_dir = Path(args.out_root) / day
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = sorted([p for p in ops_day.glob('*') if p.is_dir()]) if ops_day.exists() else []

    coverage_values = []
    skipped_sum = 0
    fallback_sum = 0
    trim_sum = 0
    policy_levels = Counter()
    offenders_counter = Counter()
    cost_guard_counter = Counter()

    run_summaries = []

    for r in runs:
        ops = _load_json(r / 'ops_run.json')
        met = _load_json(r / 'metrics.json')
        pol = _load_json(r / 'policy_decision.json')

        cov = met.get('coverage', {})
        if isinstance(cov, dict):
            coverage_values.append(float(cov.get('min', 0.0)))
            coverage_values.append(float(cov.get('p50', 0.0)))
            coverage_values.append(float(cov.get('p95', 0.0)))

        skipped_sum += int(met.get('skipped_chunks_count', 0))
        fallback_sum += int(met.get('fallback_trigger_count', 0))
        trim_sum += int(met.get('dual_guard_trim_count', 0))

        for d in pol.get('decisions', []):
            level = d.get('level', 'OK')
            policy_levels[level] += 1

        for o in met.get('offenders_topN', [])[:20]:
            doc = o.get('doc_id')
            if doc:
                offenders_counter[doc] += 1

        for e in ops.get('errors', []):
            if isinstance(e, str) and e.startswith('cost_guard'):
                cost_guard_counter[e.split(':', 1)[0]] += 1

        run_summaries.append({
            'run_id': ops.get('run_id', r.name),
            'status': ops.get('status', 'unknown'),
            'coverage_min': cov.get('min', 0.0),
            'skipped_chunks_count': met.get('skipped_chunks_count', 0),
        })

    doc_count_base = max(len(runs), 1)
    fallback_rate = round(fallback_sum / doc_count_base, 6)
    trim_rate = round(trim_sum / doc_count_base, 6)

    rollup = {
        'version': 'daily_rollup.v1',
        'script_version': SCRIPT_VERSION,
        'date': day,
        'run_count': len(runs),
        'coverage_pct': {
            'min': min(coverage_values) if coverage_values else 0.0,
            'p50': _p(coverage_values, 0.5),
            'p95': _p(coverage_values, 0.95),
        },
        'skipped_chunks_count': {'sum': skipped_sum},
        'fallback_trigger_count': {'sum': fallback_sum, 'rate_per_run': fallback_rate},
        'dual_guard_trim_count': {'sum': trim_sum, 'rate_per_run': trim_rate},
        'offenders_topN': [{'doc_id': k, 'count': v} for k, v in offenders_counter.most_common(10)],
        'cost_guard_blocked': {'count': sum(cost_guard_counter.values()), 'reasons': dict(cost_guard_counter)},
        'policy_level_distribution': dict(policy_levels),
        'top_repeated_offenders': [k for k, _ in offenders_counter.most_common(5)],
        'runs': run_summaries,
    }

    rollup_json = out_dir / 'daily_rollup.json'
    rollup_md = out_dir / 'daily_report.md'
    rollup_json.write_text(json.dumps(rollup, ensure_ascii=False, indent=2) + '\n')

    md = []
    md.append(f"# OpenViking Daily Report - {day}")
    md.append('')
    md.append(f"- Runs: {rollup['run_count']}")
    md.append(f"- Coverage min/p50/p95: {rollup['coverage_pct']['min']} / {rollup['coverage_pct']['p50']} / {rollup['coverage_pct']['p95']}")
    md.append(f"- Skipped chunks(sum): {skipped_sum}")
    md.append(f"- Fallback sum/rate: {fallback_sum} / {fallback_rate}")
    md.append(f"- Dual-guard trim sum/rate: {trim_sum} / {trim_rate}")
    md.append(f"- Cost guard blocked count: {rollup['cost_guard_blocked']['count']}")
    md.append('')
    md.append('## Policy level distribution')
    for k, v in sorted(policy_levels.items()):
        md.append(f"- {k}: {v}")
    md.append('')
    md.append('## Top offenders')
    for row in rollup['offenders_topN']:
        md.append(f"- {row['doc_id']}: {row['count']}")
    md.append('')
    md.append('## Runs')
    for r in run_summaries:
        md.append(f"- {r['run_id']}: status={r['status']} coverage_min={r['coverage_min']} skipped={r['skipped_chunks_count']}")

    rollup_md.write_text('\n'.join(md) + '\n')

    payload = {
        'daily_rollup': str(rollup_json),
        'daily_report': str(rollup_md),
        'run_count': len(runs),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Rollup: {rollup_json}\nReport: {rollup_md}\nRuns: {len(runs)}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

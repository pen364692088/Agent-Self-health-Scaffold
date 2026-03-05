#!/usr/bin/env python3
"""Cron runner for OpenViking embedding ops monitoring."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from openviking.ops.alerting import Alert, AlertManager

SCRIPT_VERSION = 'openviking_ops_cron.v1'


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        # tiny fallback parser for simple nested mappings
        data = {}
        stack = [(0, data)]
        for raw in path.read_text().splitlines():
            if not raw.strip() or raw.strip().startswith('#'):
                continue
            indent = len(raw) - len(raw.lstrip(' '))
            line = raw.strip()
            if ':' not in line:
                continue
            k, v = [x.strip() for x in line.split(':', 1)]
            while stack and indent < stack[-1][0]:
                stack.pop()
            parent = stack[-1][1]
            if v == '':
                node = {}
                parent[k] = node
                stack.append((indent + 2, node))
            else:
                if v.lower() in {'true', 'false'}:
                    parent[k] = (v.lower() == 'true')
                else:
                    try:
                        parent[k] = int(v) if v.isdigit() else float(v)
                    except Exception:
                        parent[k] = v.strip('"').strip("'")
        return data


def _json_from_cmd(cmd: list[str]) -> dict:
    code, out, err = _run(cmd)
    if code != 0:
        raise RuntimeError(f'command failed: {cmd}\n{err.strip()}')
    return json.loads(out)


def _build_alerts(*, health: dict, metrics: dict, policy: dict, root_uri: str) -> list[Alert]:
    alerts: list[Alert] = []

    status = health.get('status', 'HEALTHY')
    if status == 'ALERT':
        alerts.append(Alert(
            level='ERROR',
            rule_id='health_alert',
            root_uri=root_uri,
            reason_signature=';'.join(health.get('reasons', [])) or 'health_alert',
            message='OpenViking embedding healthcheck ALERT',
            details=health,
        ))

    skipped = int(metrics.get('skipped_chunks_count', 0))
    if skipped > 0:
        alerts.append(Alert(
            level='ERROR',
            rule_id='skipped_chunks',
            root_uri=root_uri,
            reason_signature=f'skipped={skipped}',
            message=f'skipped_chunks_count={skipped}',
            top_offender_doc_id=(metrics.get('offenders_topN') or [{}])[0].get('doc_id') if metrics.get('offenders_topN') else None,
            details={'skipped_chunks_count': skipped},
        ))

    coverage_min = float(metrics.get('coverage', {}).get('min', 1.0))
    if coverage_min < 0.90:
        alerts.append(Alert(
            level='ERROR',
            rule_id='coverage_min',
            root_uri=root_uri,
            reason_signature=f'coverage_min={coverage_min:.6f}',
            message=f'coverage_min below threshold: {coverage_min:.3f}',
            top_offender_doc_id=(metrics.get('offenders_topN') or [{}])[0].get('doc_id') if metrics.get('offenders_topN') else None,
            details={'coverage_min': coverage_min},
        ))

    # policy WARN/ERROR summaries
    levels = [d.get('level', 'OK') for d in policy.get('decisions', [])]
    warn_cnt = sum(1 for x in levels if x == 'WARN')
    err_cnt = sum(1 for x in levels if x == 'ERROR')
    if err_cnt > 0:
        alerts.append(Alert(
            level='ERROR',
            rule_id='policy_error',
            root_uri=root_uri,
            reason_signature=f'policy_error={err_cnt}',
            message=f'policy ERROR count={err_cnt}',
            details={'policy_error_count': err_cnt},
        ))
    elif warn_cnt > 0:
        alerts.append(Alert(
            level='WARN',
            rule_id='policy_warn',
            root_uri=root_uri,
            reason_signature=f'policy_warn={warn_cnt}',
            message=f'policy WARN count={warn_cnt}',
            details={'policy_warn_count': warn_cnt},
        ))

    return alerts


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='OpenViking ops cron runner')
    p.add_argument('--config', default=str(WORKSPACE / 'config' / 'openviking_ops.yaml'))
    p.add_argument('--root-uri')
    p.add_argument('--doc-ids', nargs='*', default=[])
    p.add_argument('--skip-index', action='store_true', help='Skip ingest/index refresh, use provided metrics/policy')
    p.add_argument('--metrics')
    p.add_argument('--policy')
    p.add_argument('--webhook-url')
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
        print(json.dumps({'sample': 'python scripts/openviking_ops_cron.py --root-uri viking://resources/user/memory/'}, ensure_ascii=False))
        return 0

    cfg_path = Path(args.config)
    cfg = _load_yaml(cfg_path) if cfg_path.exists() else {}

    root_uri = args.root_uri or cfg.get('root_uri', 'viking://resources/user/memory/')

    now = datetime.now(timezone.utc)
    day = now.strftime('%Y%m%d')
    run_id = f"{now.strftime('%H%M%S')}-{uuid.uuid4().hex[:8]}"
    run_dir = WORKSPACE / 'artifacts' / 'openviking' / 'ops_runs' / day / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    cfg_hash = hashlib.sha256(cfg_path.read_bytes()).hexdigest()[:16] if cfg_path.exists() else 'no_config'

    ingest_payload = None
    metrics_path = Path(args.metrics) if args.metrics else None
    policy_path = Path(args.policy) if args.policy else None

    status = 'ok'
    errors = []

    # Step 1: refresh artifacts unless skipped
    if not args.skip_index:
        cmd = ['python3', str(WORKSPACE / 'scripts' / 'openviking_ingest_index.py'), '--root-uri', root_uri, '--out-dir', str(run_dir), '--json']
        if args.doc_ids:
            cmd = ['python3', str(WORKSPACE / 'scripts' / 'openviking_ingest_index.py'), '--doc-ids', *args.doc_ids, '--out-dir', str(run_dir), '--json']
        try:
            ingest_payload = _json_from_cmd(cmd)
            metrics_path = Path(ingest_payload['metrics'])
            policy_path = Path(ingest_payload['policy_decision'])
        except Exception as e:
            status = 'failed'
            errors.append(f'index_refresh_failed:{e}')

    # Step 2: healthcheck
    health_payload = {}
    if metrics_path and policy_path and metrics_path.exists() and policy_path.exists():
        cmd = [
            'python3', str(WORKSPACE / 'scripts' / 'openviking_embedding_healthcheck.py'),
            '--metrics', str(metrics_path),
            '--policy', str(policy_path),
            '--json',
        ]
        try:
            health_payload = _json_from_cmd(cmd)
        except Exception as e:
            status = 'failed'
            errors.append(f'healthcheck_failed:{e}')
    else:
        status = 'failed'
        errors.append('missing_metrics_or_policy')

    # Step 3: alerting (never breaks main flow)
    alert_results = []
    retry_summary = {'retried': 0, 'delivered': 0, 'kept': 0}
    alert_cfg = cfg.get('alerting', {}) if isinstance(cfg.get('alerting', {}), dict) else {}
    alerting_enabled = bool(alert_cfg.get('enabled', True))

    if alerting_enabled:
        webhook = args.webhook_url or alert_cfg.get('webhook_url') or None
        manager = AlertManager(
            state_path=WORKSPACE / 'artifacts' / 'openviking' / 'alert_state.json',
            failed_dir=WORKSPACE / 'artifacts' / 'openviking' / 'alerts' / 'failed',
            cooldown_warn_sec=int(alert_cfg.get('cooldown_warn_sec', 3600)),
            cooldown_error_sec=int(alert_cfg.get('cooldown_error_sec', 600)),
            webhook_url=webhook,
        )

        try:
            metrics_data = json.loads(metrics_path.read_text()) if metrics_path and metrics_path.exists() else {}
            policy_data = json.loads(policy_path.read_text()) if policy_path and policy_path.exists() else {}
            alerts = _build_alerts(health=health_payload, metrics=metrics_data, policy=policy_data, root_uri=root_uri)

            push_warn = bool(alert_cfg.get('push_warn', True))
            push_warn_soft = bool(alert_cfg.get('push_warn_soft', False))

            for a in alerts:
                if a.level == 'WARN_SOFT' and not push_warn_soft:
                    continue
                if a.level == 'WARN' and not push_warn:
                    continue
                alert_results.append(manager.send(a))

            retry_summary = manager.retry_failed(max_items=20)
        except Exception as e:
            alert_results.append({'sent': False, 'reason': f'alerting_exception:{e}'})

    # Step 4: ops_run audit
    ops_run = {
        'version': 'ops_run.v1',
        'script_version': SCRIPT_VERSION,
        'run_id': run_id,
        'started_at': now.isoformat(),
        'ended_at': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'errors': errors,
        'inputs': {
            'root_uri': root_uri,
            'doc_ids': args.doc_ids,
            'config': str(cfg_path),
            'config_hash': cfg_hash,
        },
        'artifacts': {
            'run_dir': str(run_dir),
            'metrics': str(metrics_path) if metrics_path else None,
            'policy': str(policy_path) if policy_path else None,
            'health': str(run_dir / 'healthcheck_result.json'),
        },
        'health': health_payload,
        'alerting': {
            'enabled': alerting_enabled,
            'results': alert_results,
            'retry': retry_summary,
        },
    }

    (run_dir / 'ops_run.json').write_text(json.dumps(ops_run, ensure_ascii=False, indent=2) + '\n')
    (run_dir / 'healthcheck_result.json').write_text(json.dumps(health_payload, ensure_ascii=False, indent=2) + '\n')

    if args.json:
        print(json.dumps(ops_run, ensure_ascii=False, indent=2))
    else:
        print(f'Ops run complete: {run_dir}')

    # preserve run artifacts even on failure
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

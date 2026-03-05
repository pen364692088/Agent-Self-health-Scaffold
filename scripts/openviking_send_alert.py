#!/usr/bin/env python3
"""Manual alert sender for channel validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from openviking.ops.alerting import Alert, AlertManager

SCRIPT_VERSION = 'openviking_send_alert.v1'


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Send one OpenViking alert')
    p.add_argument('--level', default='WARN')
    p.add_argument('--rule-id', default='manual_test')
    p.add_argument('--root-uri', default='viking://resources/user/memory/')
    p.add_argument('--reason-signature', default='manual')
    p.add_argument('--message', default='Manual OpenViking alert test')
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
        print(json.dumps({'sample': 'python scripts/openviking_send_alert.py --webhook-url https://...'}, ensure_ascii=False))
        return 0

    manager = AlertManager(
        state_path=WORKSPACE / 'artifacts' / 'openviking' / 'alert_state.json',
        failed_dir=WORKSPACE / 'artifacts' / 'openviking' / 'alerts' / 'failed',
        webhook_url=args.webhook_url,
    )

    alert = Alert(
        level=args.level,
        rule_id=args.rule_id,
        root_uri=args.root_uri,
        reason_signature=args.reason_signature,
        message=args.message,
    )

    result = manager.send(alert)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

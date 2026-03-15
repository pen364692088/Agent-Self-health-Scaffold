#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from recovery_orchestrator import RecoveryOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    orchestrator = RecoveryOrchestrator(args.root)
    decisions = [d.to_dict() for d in orchestrator.scan()]
    out = {
        'status': 'ok',
        'decision_count': len(decisions),
        'decisions': decisions,
    }
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for d in decisions:
            print(f"{d['task_id']} {d['run_id']} -> {d['action']} ({d['reason']})")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reconciler import apply_recovery_scan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    applied = apply_recovery_scan(args.root)
    out = {
        "status": "ok",
        "applied_count": len(applied),
        "applied": [x.to_dict() for x in applied],
    }
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for item in applied:
            print(f"{item.task_id} {item.run_id} -> {item.action} [{item.status}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

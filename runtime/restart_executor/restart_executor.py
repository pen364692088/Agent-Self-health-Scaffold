"""
Out-of-band Restart Executor

Ensures restart operations execute outside the current exec chain,
preventing SIGTERM interruption of running tasks.
"""
from __future__ import annotations

import json
import subprocess
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional, Any
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.task_ledger import TaskLedger

RESTART_INTENTS_DIR = "artifacts/restart_intents"
COOLDOWN_DEFAULT_SEC = 60


@dataclass
class RestartIntent:
    intent_id: str
    target: str  # gateway | worker | all
    reason: str  # stalled | drift_detected | manual | scheduled
    trigger_run_id: Optional[str]
    requested_at: str
    cooldown_until: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RestartIntent":
        return cls(**d)


@dataclass
class RestartResult:
    intent_id: str
    status: str  # pending | executing | completed | failed
    executed_at: Optional[str]
    recovery_triggered: bool
    error: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RestartExecutor:
    """Out-of-band restart executor with cooldown protection."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.intents_dir = self.root / RESTART_INTENTS_DIR
        self.intents_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = TaskLedger(self.root)

    def submit_restart_intent(
        self,
        target: str,
        reason: str,
        trigger_run_id: Optional[str] = None,
        cooldown_sec: int = COOLDOWN_DEFAULT_SEC,
    ) -> str:
        """Submit a restart intent for out-of-band execution."""
        # Check for recent restart (cooldown)
        recent = self._get_recent_intent(target)
        if recent and recent.cooldown_until:
            try:
                cooldown_ts = datetime.fromisoformat(recent.cooldown_until.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if now < cooldown_ts:
                    raise RuntimeError(f"Cooldown active until {recent.cooldown_until}")
            except RuntimeError:
                raise
            except Exception:
                pass

        intent_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        cooldown_until = now + timedelta(seconds=cooldown_sec)

        intent = RestartIntent(
            intent_id=intent_id,
            target=target,
            reason=reason,
            trigger_run_id=trigger_run_id,
            requested_at=now.isoformat().replace("+00:00", "Z"),
            cooldown_until=cooldown_until.isoformat().replace("+00:00", "Z"),
        )

        # Persist intent
        intent_path = self.intents_dir / f"{intent_id}.json"
        with intent_path.open("w") as f:
            json.dump(intent.to_dict(), f, indent=2)

        # Write to ledger
        self._log_restart_intent(intent)

        # Execute out-of-band via systemd or background process
        self._execute_out_of_band(intent)

        return intent_id

    def check_restart_status(self, intent_id: str) -> RestartResult:
        """Check the status of a restart intent."""
        intent_path = self.intents_dir / f"{intent_id}.json"
        result_path = self.intents_dir / f"{intent_id}_result.json"

        if not intent_path.exists():
            raise FileNotFoundError(f"Intent {intent_id} not found")

        if result_path.exists():
            with result_path.open() as f:
                return RestartResult(**json.load(f))

        # Still pending
        return RestartResult(
            intent_id=intent_id,
            status="pending",
            executed_at=None,
            recovery_triggered=False,
            error=None,
        )

    def _execute_out_of_band(self, intent: RestartIntent) -> None:
        """Execute restart out-of-band using systemd or background script."""
        # Write result immediately as executing
        result = RestartResult(
            intent_id=intent.intent_id,
            status="executing",
            executed_at=None,
            recovery_triggered=False,
            error=None,
        )
        self._write_result(result)

        # Use systemd-run for out-of-band execution
        try:
            script = self._generate_restart_script(intent)
            script_path = self.intents_dir / f"{intent.intent_id}_exec.sh"
            with script_path.open("w") as f:
                f.write(script)
            script_path.chmod(0o755)

            # Execute via systemd-run or nohup
            subprocess.Popen(
                [str(script_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            self._write_result(result)

    def _generate_restart_script(self, intent: RestartIntent) -> str:
        """Generate shell script for restart execution."""
        return f'''#!/bin/bash
# Out-of-band restart executor
# Intent: {intent.intent_id}
# Target: {intent.target}
# Reason: {intent.reason}

set -e

# Wait a moment for current process to detach
sleep 2

# Execute restart based on target
case "{intent.target}" in
    gateway)
        openclaw gateway restart 2>/dev/null || systemctl --user restart openclaw-gateway 2>/dev/null || true
        ;;
    worker)
        systemctl --user restart openclaw-worker 2>/dev/null || true
        ;;
    all)
        openclaw gateway restart 2>/dev/null || systemctl --user restart openclaw-gateway 2>/dev/null || true
        systemctl --user restart openclaw-worker 2>/dev/null || true
        ;;
esac

# Write completion result
RESULT_PATH="{self.intents_dir}/{intent.intent_id}_result.json"
cat > "$RESULT_PATH" << EOF
{{"intent_id": "{intent.intent_id}", "status": "completed", "executed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "recovery_triggered": true, "error": null}}
EOF

# Trigger recovery apply (scan + durable continuation events)
cd {self.root}
python3 runtime/recovery-orchestrator/recovery_apply.py --root {self.root} 2>/dev/null || true
'''

    def _write_result(self, result: RestartResult) -> None:
        result_path = self.intents_dir / f"{result.intent_id}_result.json"
        with result_path.open("w") as f:
            json.dump(result.to_dict(), f, indent=2)

    def _get_recent_intent(self, target: str) -> Optional[RestartIntent]:
        """Get most recent intent for target within cooldown window."""
        intents = []
        for path in self.intents_dir.glob("*.json"):
            if "_result" in path.name:
                continue
            try:
                with path.open() as f:
                    data = json.load(f)
                if data.get("target") == target:
                    intents.append(RestartIntent.from_dict(data))
            except Exception:
                continue

        if not intents:
            return None

        # Return most recent
        return sorted(intents, key=lambda i: i.requested_at, reverse=True)[0]

    def _log_restart_intent(self, intent: RestartIntent) -> None:
        """Log restart intent to ledger."""
        if intent.trigger_run_id:
            event = {
                "event_id": f"evt-restart-{intent.intent_id}",
                "task_id": "system",
                "run_id": intent.trigger_run_id,
                "type": "restart_intent_created",
                "ts": intent.requested_at,
                "payload": intent.to_dict(),
                "idempotency_key": f"restart-{intent.intent_id}",
            }
            self.ledger.append_event(event)


def submit_restart_intent(
    root: Path | str,
    target: str,
    reason: str,
    trigger_run_id: Optional[str] = None,
) -> str:
    """Convenience function to submit restart intent."""
    executor = RestartExecutor(root)
    return executor.submit_restart_intent(target, reason, trigger_run_id)


def check_restart_status(root: Path | str, intent_id: str) -> RestartResult:
    """Convenience function to check restart status."""
    executor = RestartExecutor(root)
    return executor.check_restart_status(intent_id)

"""Deterministic MVP11 loop used by replay/eval/soak tooling.

This is intentionally lightweight so CI can execute it fast while still
producing stable, auditable artifacts.
"""

from __future__ import annotations

import json
import random
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from emotiond.science.interventions import InterventionType


class LoopMVP10:
    def __init__(
        self,
        seed: int = 42,
        artifacts_dir: str = "artifacts/mvp11",
        use_mock_planner: bool = True,
        intervention: Optional[str] = None,
    ) -> None:
        self.seed = seed
        self._rng = random.Random(seed)
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.use_mock_planner = use_mock_planner
        self.intervention = intervention

        self.run_id: Optional[str] = None
        self.goals: List[str] = []
        self.ticks_executed = 0
        self._log_fp = None
        self._last_focus: Optional[str] = None

    @property
    def ledger(self) -> "LoopMVP10":
        # Backward-compatible accessor used by older scripts.
        return self

    def _new_run_id(self) -> str:
        ts = int(time.time())
        return f"mvp11_{ts}_{uuid.uuid4().hex[:8]}"

    def start(self, goals: Optional[List[str]] = None) -> None:
        self.run_id = self._new_run_id()
        self.goals = goals or [f"goal_{i}" for i in range(8)]
        self.ticks_executed = 0
        self._last_focus = None

        log_path = self.artifacts_dir / f"{self.run_id}.jsonl"
        self._log_fp = log_path.open("w", encoding="utf-8")

    def _apply_intervention(self, state: Dict[str, float], event: Dict[str, Any]) -> None:
        kind = self.intervention
        if not kind:
            return

        event["intervention"] = kind

        if kind == InterventionType.DISABLE_BROADCAST.value:
            # Less stable focus/planning consistency.
            event["validation"]["replan_count"] = max(1, event["validation"]["replan_count"] + 1)
            event["plan"]["coherence"] = max(0.0, event["plan"]["coherence"] - 0.3)

        elif kind == InterventionType.DISABLE_HOMEOSTASIS.value:
            # Increase drift from nominal setpoint.
            for k in state:
                state[k] = max(0.0, min(1.0, state[k] + self._rng.uniform(-0.22, 0.22)))

        elif kind == InterventionType.REMOVE_SELF_STATE.value:
            event["self_state_missing"] = True
            event["validation"]["replan_count"] += 1
            event["plan"]["self_consistency"] = 0.25

        elif kind == InterventionType.OPEN_LOOP.value:
            event["plan"]["closed_loop"] = False
            event["governor_decision"]["decision"] = "REQUIRE_APPROVAL"
            event["validation"]["replan_count"] += 1

    def tick(self) -> Dict[str, Any]:
        if not self.run_id or self._log_fp is None:
            raise RuntimeError("Loop not started; call start() first")

        tick_no = self.ticks_executed + 1
        focus = self._rng.choice(self.goals)
        action_type = self._rng.choice(["observe", "nudge", "repair", "stabilize"]) if self.use_mock_planner else "observe"

        replan_count = 1 if self._rng.random() < 0.08 else 0
        decision = "ALLOW"
        if self._rng.random() < 0.03:
            decision = "DENY"

        homeostasis = {
            "energy": max(0.0, min(1.0, 0.75 + self._rng.uniform(-0.08, 0.08))),
            "safety": max(0.0, min(1.0, 0.75 + self._rng.uniform(-0.08, 0.08))),
            "affiliation": max(0.0, min(1.0, 0.75 + self._rng.uniform(-0.08, 0.08))),
            "certainty": max(0.0, min(1.0, 0.75 + self._rng.uniform(-0.08, 0.08))),
            "autonomy": max(0.0, min(1.0, 0.75 + self._rng.uniform(-0.08, 0.08))),
            "fairness": max(0.0, min(1.0, 0.75 + self._rng.uniform(-0.08, 0.08))),
        }

        event: Dict[str, Any] = {
            "tick": tick_no,
            "ts": round(time.time(), 6),
            "run_id": self.run_id,
            "seed": self.seed,
            "chosen_focus": focus,
            "focus_switch": bool(self._last_focus is not None and self._last_focus != focus),
            "action": {"type": action_type},
            "validation": {"replan_count": replan_count},
            "plan": {
                "replan_count": replan_count,
                "coherence": round(max(0.0, min(1.0, 0.88 + self._rng.uniform(-0.05, 0.05))), 4),
                "self_consistency": round(max(0.0, min(1.0, 0.92 + self._rng.uniform(-0.04, 0.04))), 4),
                "closed_loop": True,
            },
            "governor_decision": {"decision": decision},
            "homeostasis_state": homeostasis,
        }

        self._apply_intervention(homeostasis, event)

        self._log_fp.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._log_fp.flush()

        self._last_focus = focus
        self.ticks_executed = tick_no
        return event

    def stop(self) -> Dict[str, Any]:
        if not self.run_id:
            raise RuntimeError("Loop not started")

        if self._log_fp:
            self._log_fp.close()
            self._log_fp = None

        summary = {
            "run_id": self.run_id,
            "seed": self.seed,
            "ticks_executed": self.ticks_executed,
            "goals": self.goals,
            "goals_count": len(self.goals),
            "intervention": self.intervention,
            "artifacts_dir": str(self.artifacts_dir),
            "ts": time.time(),
        }

        summary_path = self.artifacts_dir / f"summary_{self.run_id}.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return summary

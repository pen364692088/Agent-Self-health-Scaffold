"""Intervention controls for MVP11 causal evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class InterventionType(str, Enum):
    DISABLE_BROADCAST = "disable_broadcast"
    DISABLE_HOMEOSTASIS = "disable_homeostasis"
    REMOVE_SELF_STATE = "remove_self_state"
    OPEN_LOOP = "open_loop"


@dataclass
class Intervention:
    kind: InterventionType
    payload: Dict[str, Any] = field(default_factory=dict)


class InterventionManager:
    """Small in-memory intervention registry used by MVP11 scripts/tests."""

    def __init__(self) -> None:
        self._active: Dict[InterventionType, Intervention] = {}

    def enable(self, kind: InterventionType, payload: Dict[str, Any] | None = None) -> None:
        self._active[kind] = Intervention(kind=kind, payload=payload or {})

    def disable(self, kind: InterventionType) -> None:
        self._active.pop(kind, None)

    def clear(self) -> None:
        self._active.clear()

    def is_active(self, kind: InterventionType) -> bool:
        return kind in self._active

    # Common convenience predicates used by prior MVP11 code paths.
    def is_broadcast_disabled(self) -> bool:
        return self.is_active(InterventionType.DISABLE_BROADCAST)

    def is_homeostasis_disabled(self) -> bool:
        return self.is_active(InterventionType.DISABLE_HOMEOSTASIS)

    def is_self_state_removed(self) -> bool:
        return self.is_active(InterventionType.REMOVE_SELF_STATE)

    def is_open_loop_active(self) -> bool:
        return self.is_active(InterventionType.OPEN_LOOP)

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {k.value: v.payload for k, v in self._active.items()}

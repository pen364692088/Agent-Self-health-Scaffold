"""
Canonical Adapter - Real Ledger Integration (Shadow Mode)

Provides read-only access to canonical sources for shadow comparison.
Does NOT replace bridge state; generates compare reports only.

v0 Constraints:
- Read-only access to ledger/run_state
- No write-back to any source
- Shadow compare output only
- Does not replace MaterializedState as primary source

Sources:
- TASK_LEDGER.jsonl (task events)
- state/durable_execution/RUN_STATE.json (durable run state)
- artifacts/run_ledger/*.jsonl (run event streams)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class CanonicalSource:
    """Information about a canonical source."""
    name: str
    path: str
    exists: bool
    last_modified: Optional[str] = None
    record_count: Optional[int] = None
    error: Optional[str] = None


@dataclass
class CanonicalField:
    """A field from canonical source."""
    name: str
    value: Optional[Any]
    source: str
    raw: Optional[Any] = None
    status: str = "valid"  # 'valid', 'empty', 'missing', 'error'


@dataclass
class FieldComparison:
    """Comparison between bridge and canonical for a single field."""
    field_name: str
    bridge_value: Optional[Any]
    canonical_value: Optional[Any]
    bridge_source: Optional[str]
    canonical_source: Optional[str]
    match: bool
    conflict_type: Optional[str] = None  # 'value_mismatch', 'source_mismatch', 'canonical_missing', 'bridge_missing'
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShadowCompareReport:
    """Complete shadow comparison report."""
    generated_at: str
    bridge_state: Dict[str, Any]
    canonical_state: Dict[str, Any]
    field_comparisons: Dict[str, FieldComparison]
    coverage: Dict[str, Any]  # Which fields are covered by which source
    conflicts: List[Dict[str, Any]]
    fallbacks: List[Dict[str, Any]]
    warnings: List[str]
    summary: Dict[str, Any]
    sources: Dict[str, CanonicalSource]


# =============================================================================
# Canonical Adapter (Shadow Mode)
# =============================================================================

class CanonicalAdapter:
    """
    Read-only adapter to canonical sources.
    
    v0: Shadow mode only - does not replace bridge state.
    Generates comparison reports for observability.
    """
    
    def __init__(
        self,
        workspace_path: Optional[Path] = None,
        task_ledger_path: Optional[Path] = None,
        run_state_path: Optional[Path] = None,
        run_ledger_dir: Optional[Path] = None
    ):
        self.workspace = workspace_path or Path("/home/moonlight/.openclaw/workspace")
        
        # Default paths
        self.task_ledger_path = task_ledger_path or self.workspace / "TASK_LEDGER.jsonl"
        self.run_state_path = run_state_path or self.workspace / "state" / "durable_execution" / "RUN_STATE.json"
        self.run_ledger_dir = run_ledger_dir or self.workspace / "artifacts" / "run_ledger"
        
        self._connected = False
        self._sources: Dict[str, CanonicalSource] = {}
    
    def connect(self) -> bool:
        """
        Connect to canonical sources (verify they exist).
        
        Returns True if at least one source is available.
        """
        self._sources = {}
        
        # Check task ledger
        self._sources["task_ledger"] = CanonicalSource(
            name="task_ledger",
            path=str(self.task_ledger_path),
            exists=self.task_ledger_path.exists()
        )
        if self._sources["task_ledger"].exists:
            self._sources["task_ledger"].last_modified = datetime.fromtimestamp(
                self.task_ledger_path.stat().st_mtime
            ).isoformat()
            self._sources["task_ledger"].record_count = self._count_lines(self.task_ledger_path)
        
        # Check run state
        self._sources["run_state"] = CanonicalSource(
            name="run_state",
            path=str(self.run_state_path),
            exists=self.run_state_path.exists()
        )
        if self._sources["run_state"].exists:
            self._sources["run_state"].last_modified = datetime.fromtimestamp(
                self.run_state_path.stat().st_mtime
            ).isoformat()
        
        # Check run ledger dir
        self._sources["run_ledger_dir"] = CanonicalSource(
            name="run_ledger_dir",
            path=str(self.run_ledger_dir),
            exists=self.run_ledger_dir.exists()
        )
        if self._sources["run_ledger_dir"].exists:
            jsonl_files = list(self.run_ledger_dir.glob("*.jsonl"))
            self._sources["run_ledger_dir"].record_count = len(jsonl_files)
        
        # Connected if any source exists
        self._connected = any(s.exists for s in self._sources.values())
        return self._connected
    
    def is_connected(self) -> bool:
        """Check if adapter is connected."""
        return self._connected
    
    def get_sources(self) -> Dict[str, CanonicalSource]:
        """Get information about canonical sources."""
        return self._sources
    
    def read_task_ledger(self, lookback_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Read recent task ledger entries.
        
        Read-only; does not modify the ledger.
        """
        if not self.task_ledger_path.exists():
            return []
        
        entries = []
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        
        try:
            with self.task_ledger_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        # Filter by timestamp if available
                        ts_str = entry.get("ts")
                        if ts_str:
                            try:
                                ts = datetime.fromisoformat(ts_str)
                                if ts < cutoff:
                                    continue
                            except Exception:
                                pass
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self._sources.get("task_ledger", CanonicalSource(name="task_ledger", path="", exists=False)).error = str(e)
        
        return entries
    
    def read_run_state(self) -> Dict[str, Any]:
        """
        Read durable run state.
        
        Read-only; does not modify the state.
        """
        if not self.run_state_path.exists():
            return {}
        
        try:
            return json.loads(self.run_state_path.read_text())
        except Exception as e:
            return {"error": str(e)}
    
    def extract_canonical_fields(self) -> Dict[str, CanonicalField]:
        """
        Extract fields from canonical sources.
        
        Returns a dictionary of field name -> CanonicalField.
        """
        fields = {}
        
        # Extract from run_state
        run_state = self.read_run_state()
        if run_state and "error" not in run_state:
            # Objective
            fields["objective"] = CanonicalField(
                name="objective",
                value=run_state.get("objective"),
                source="run_state",
                status="valid" if run_state.get("objective") else "empty"
            )
            
            # Status (maps to phase)
            fields["status"] = CanonicalField(
                name="status",
                value=run_state.get("status"),
                source="run_state",
                status="valid" if run_state.get("status") else "empty"
            )
            
            # Next step
            next_step = run_state.get("next_step")
            if not next_step and run_state.get("last_checkpoint"):
                next_step = run_state["last_checkpoint"].get("next_step")
            fields["next_step"] = CanonicalField(
                name="next_step",
                value=next_step,
                source="run_state",
                status="valid" if next_step else "empty"
            )
            
            # Hard block (maps to blocker)
            if run_state.get("hard_block"):
                fields["blocker"] = CanonicalField(
                    name="blocker",
                    value=run_state.get("hard_block_reason") or "hard_block",
                    source="run_state",
                    status="valid"
                )
            
            # Resume action
            fields["resume_action"] = CanonicalField(
                name="resume_action",
                value=run_state.get("resume_action"),
                source="run_state",
                status="valid" if run_state.get("resume_action") else "empty"
            )
        
        # Extract from task ledger (latest task)
        ledger_entries = self.read_task_ledger(lookback_hours=24)
        if ledger_entries:
            # Filter out test entries
            real_entries = [
                e for e in ledger_entries
                if not str(e.get("task_id", "")).startswith("test_")
                and "测试" not in str(e.get("description", ""))
                and e.get("parent_session_key") != "agent:main:test"
            ]
            
            if real_entries:
                latest = real_entries[-1]
                
                # Task ID as identifier
                fields["latest_task_id"] = CanonicalField(
                    name="latest_task_id",
                    value=latest.get("task_id"),
                    source="task_ledger",
                    status="valid" if latest.get("task_id") else "empty"
                )
                
                # Task state
                fields["latest_task_state"] = CanonicalField(
                    name="latest_task_state",
                    value=latest.get("state"),
                    source="task_ledger",
                    status="valid" if latest.get("state") else "empty"
                )
        
        return fields
    
    def shadow_compare(
        self,
        bridge_state: Dict[str, Any]
    ) -> ShadowCompareReport:
        """
        Compare bridge state with canonical state.
        
        This is a SHADOW comparison - does not replace bridge state.
        Generates a report showing coverage, conflicts, and fallbacks.
        
        Args:
            bridge_state: The MaterializedState as dict from bridge sources
        
        Returns:
            ShadowCompareReport with detailed comparison
        """
        if not self._connected:
            self.connect()
        
        canonical_fields = self.extract_canonical_fields()
        
        comparisons: Dict[str, FieldComparison] = {}
        conflicts = []
        fallbacks = []
        warnings = []
        
        # Fields to compare
        comparable_fields = ["objective", "phase", "status", "blocker", "next_step"]
        
        for field_name in comparable_fields:
            bridge_value = bridge_state.get(field_name)
            bridge_source = None
            
            # Get bridge source from field_resolutions
            if field_name in bridge_state.get("field_resolutions", {}):
                fr = bridge_state["field_resolutions"][field_name]
                bridge_source = fr.get("chosen_source")
            
            # Map phase to status for comparison
            canonical_field_name = field_name
            if field_name == "phase":
                canonical_field_name = "status"
            
            canonical_field = canonical_fields.get(canonical_field_name)
            canonical_value = canonical_field.value if canonical_field else None
            canonical_source = canonical_field.source if canonical_field else None
            
            # Determine match
            match = self._values_match(bridge_value, canonical_value)
            
            # Determine conflict type
            conflict_type = None
            if bridge_value and canonical_value and not match:
                conflict_type = "value_mismatch"
            elif bridge_value and not canonical_value:
                conflict_type = "canonical_missing"
            elif not bridge_value and canonical_value:
                conflict_type = "bridge_missing"
            
            # Build provenance
            provenance = {
                "bridge_raw": bridge_state.get("field_sources", {}).get(field_name, {}),
                "canonical_raw": {
                    "value": canonical_value,
                    "source": canonical_source,
                    "status": canonical_field.status if canonical_field else "missing"
                }
            }
            
            comparison = FieldComparison(
                field_name=field_name,
                bridge_value=bridge_value,
                canonical_value=canonical_value,
                bridge_source=bridge_source,
                canonical_source=canonical_source,
                match=match,
                conflict_type=conflict_type,
                provenance=provenance
            )
            
            comparisons[field_name] = comparison
            
            # Track conflicts
            if conflict_type == "value_mismatch":
                conflicts.append({
                    "field": field_name,
                    "bridge_value": bridge_value,
                    "canonical_value": canonical_value,
                    "bridge_source": bridge_source,
                    "canonical_source": canonical_source
                })
            
            # Track fallbacks (canonical has value but bridge doesn't)
            if conflict_type == "bridge_missing" and canonical_value:
                fallbacks.append({
                    "field": field_name,
                    "canonical_value": canonical_value,
                    "canonical_source": canonical_source,
                    "note": "Canonical source has value not available in bridge"
                })
        
        # Build coverage report
        coverage = {
            "bridge_only": [],
            "canonical_only": [],
            "both": [],
            "neither": []
        }
        
        for field_name in comparable_fields:
            comp = comparisons[field_name]
            if comp.bridge_value and comp.canonical_value:
                coverage["both"].append(field_name)
            elif comp.bridge_value:
                coverage["bridge_only"].append(field_name)
            elif comp.canonical_value:
                coverage["canonical_only"].append(field_name)
            else:
                coverage["neither"].append(field_name)
        
        # Add warnings
        if coverage["neither"]:
            warnings.append(f"Fields missing in both sources: {', '.join(coverage['neither'])}")
        
        if conflicts:
            warnings.append(f"Value conflicts detected: {len(conflicts)} fields")
        
        # Build summary
        summary = {
            "total_fields_compared": len(comparable_fields),
            "matches": sum(1 for c in comparisons.values() if c.match),
            "conflicts": len(conflicts),
            "fallbacks_available": len(fallbacks),
            "bridge_coverage": len(coverage["bridge_only"]) + len(coverage["both"]),
            "canonical_coverage": len(coverage["canonical_only"]) + len(coverage["both"]),
            "uncertainty_flag": bridge_state.get("uncertainty_flag", False)
        }
        
        return ShadowCompareReport(
            generated_at=datetime.now().isoformat(),
            bridge_state=bridge_state,
            canonical_state={name: {"value": f.value, "source": f.source} for name, f in canonical_fields.items()},
            field_comparisons=comparisons,
            coverage=coverage,
            conflicts=conflicts,
            fallbacks=fallbacks,
            warnings=warnings,
            summary=summary,
            sources=self._sources
        )
    
    def merge_with_canonical(self, bridge_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        STUB: In v0, this does NOT merge.
        
        Returns the bridge_state unchanged.
        Shadow comparison should be done separately via shadow_compare().
        """
        # v0: Return unchanged
        # Future: Merge canonical values into bridge_state with conflict resolution
        return bridge_state
    
    def _count_lines(self, path: Path) -> int:
        """Count non-empty lines in a file."""
        try:
            with path.open("r") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0
    
    def _values_match(self, v1: Any, v2: Any) -> bool:
        """Check if two values match (with normalization)."""
        if v1 is None and v2 is None:
            return True
        if v1 is None or v2 is None:
            return False
        
        # String comparison with normalization
        s1 = str(v1).strip().lower()
        s2 = str(v2).strip().lower()
        
        # Handle "none" as equivalent to None
        if s1 in ("none", "null", "n/a", ""):
            s1 = None
        if s2 in ("none", "null", "n/a", ""):
            s2 = None
        
        if s1 is None and s2 is None:
            return True
        if s1 is None or s2 is None:
            return False
        
        return s1 == s2


# =============================================================================
# Convenience Function
# =============================================================================

def create_shadow_report(
    bridge_state: Dict[str, Any],
    workspace_path: Optional[Path] = None
) -> ShadowCompareReport:
    """
    Create a shadow comparison report.
    
    Args:
        bridge_state: MaterializedState as dict
        workspace_path: Path to workspace
    
    Returns:
        ShadowCompareReport
    """
    adapter = CanonicalAdapter(workspace_path=workspace_path)
    adapter.connect()
    return adapter.shadow_compare(bridge_state)

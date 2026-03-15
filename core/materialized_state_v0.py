"""
Materialized State v0 - Core Module

Read-only state materialization from SESSION-STATE.md and working-buffer.md.
Designed for reuse by: CLI tools, prompt assembly, recovery flows, tests.

v0 Scope (FROZEN):
- Input: SESSION-STATE.md, working-buffer.md (root level only)
- Output: MaterializedState dataclass
- No handoff/capsule/summary/distill integration
- No write-back to continuity sources
- No second live state

Contract:
- All field extraction is read-only
- No side effects on source files
- Deterministic output for same input
- Semantic validation via schema
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Schema Definition (v0)
# =============================================================================

@dataclass
class FieldSource:
    """Source information for a field value."""
    status: str  # 'valid', 'empty', 'missing'
    value: Optional[str]
    raw: Optional[str] = None
    source_file: Optional[str] = None


@dataclass
class ConflictInfo:
    """Information about a field conflict."""
    source: str
    value: str
    priority: int


@dataclass
class FieldResolution:
    """Resolved field value with conflict info."""
    status: str  # 'valid', 'missing'
    value: Optional[str] = None
    chosen_source: Optional[str] = None
    reason: Optional[str] = None
    conflicts: Optional[List[ConflictInfo]] = None


@dataclass
class MaterializedState:
    """
    Materialized state from continuity sources.
    
    v0 fields (frozen):
    - objective: Current task objective
    - phase: Current phase
    - branch: Current git branch
    - blocker: Current blocker (if any)
    - next_step: Next action to take
    - next_actions: List of next actions
    
    Metadata:
    - materialized_at: Timestamp of materialization
    - sources_checked: Which sources were checked
    - uncertainty_flag: True if critical fields are missing
    """
    # Core fields
    objective: Optional[str] = None
    phase: Optional[str] = None
    branch: Optional[str] = None
    blocker: Optional[str] = None
    next_step: Optional[str] = None
    next_actions: Optional[List[str]] = None
    
    # Field-level details
    field_sources: Dict[str, FieldSource] = field(default_factory=dict)
    field_resolutions: Dict[str, FieldResolution] = field(default_factory=dict)
    
    # Metadata
    materialized_at: Optional[str] = None
    sources_checked: List[str] = field(default_factory=list)
    uncertainty_flag: bool = False
    recovery_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        
        # Simple fields
        result['objective'] = self.objective
        result['phase'] = self.phase
        result['branch'] = self.branch
        result['blocker'] = self.blocker
        result['next_step'] = self.next_step
        result['next_actions'] = self.next_actions
        result['materialized_at'] = self.materialized_at
        result['sources_checked'] = self.sources_checked
        result['uncertainty_flag'] = self.uncertainty_flag
        result['recovery_required'] = self.recovery_required
        
        # Convert nested dataclasses
        result['field_sources'] = {}
        for field_name, sources in self.field_sources.items():
            result['field_sources'][field_name] = {}
            for source_name, source_info in sources.items():
                if isinstance(source_info, FieldSource):
                    result['field_sources'][field_name][source_name] = {
                        'status': source_info.status,
                        'value': source_info.value,
                        'raw': source_info.raw,
                        'source_file': source_info.source_file
                    }
                else:
                    result['field_sources'][field_name][source_name] = source_info
        
        result['field_resolutions'] = {}
        for field_name, resolution in self.field_resolutions.items():
            if isinstance(resolution, FieldResolution):
                res_dict = {
                    'status': resolution.status,
                    'value': resolution.value,
                    'chosen_source': resolution.chosen_source,
                    'reason': resolution.reason,
                    'conflicts': None
                }
                if resolution.conflicts:
                    res_dict['conflicts'] = [
                        {'source': c.source, 'value': c.value, 'priority': c.priority}
                        for c in resolution.conflicts
                    ]
                result['field_resolutions'][field_name] = res_dict
            else:
                result['field_resolutions'][field_name] = resolution
        
        return result


# =============================================================================
# Constants
# =============================================================================

# Fields tracked for conflict resolution
TRACKED_FIELDS = ["objective", "phase", "branch", "blocker", "next_step", "next_actions"]

# Source priority (higher = more trusted)
SOURCE_PRIORITY = {
    "repo_evidence": 100,
    "wal_entry": 90,
    "handoff_md": 80,
    "session_state_md": 70,
    "working_buffer_md": 60,
}

# Placeholder values to treat as empty
PLACEHOLDER_VALUES = {"", "tbd", "n/a", "无", "none", "-", "...", "未定义", "待定"}

# Field patterns for extraction
FIELD_PATTERNS = {
    "objective": [
        r'^##\s+Current\s+Objective',
        r'^##\s+Objective',
        r'^\*\*Current\s+Objective\*\*',
        r'^\*\*Objective\*\*',
        r'^Objective[:：]',
        r'^-\s*Objective[:：]',
    ],
    "phase": [
        r'^##\s+Phase',
        r'^\*\*Phase\*\*[:：]?',
        r'^Phase[:：]',
        r'^-\s*Phase[:：]',
    ],
    "branch": [
        r'^##\s+Branch',
        r'^\*\*Branch\*\*[:：]?',
        r'^Branch[:：]',
        r'^-\s*Branch[:：]',
    ],
    "blocker": [
        r'^##\s+Blocker',
        r'^\*\*Blocker\*\*[:：]?',
        r'^Blocker[:：]',
        r'^-\s*Blocker[:：]',
    ],
    "next_step": [
        r'^##\s+Next\s+Action',
        r'^##\s+Next\s+Step',
        r'^\*\*Next\s+Action\*\*',
        r'^\*\*Next\s+Step\*\*',
        r'^Next\s+Action[:：]',
        r'^Next\s+Step[:：]',
        r'^-\s*Next\s+Action[:：]',
        r'^-\s*Next\s+Step[:：]',
    ],
    "next_actions": [
        r'^##\s+Next\s+Actions',
        r'^\*\*Next\s+Actions\*\*',
        r'^Next\s+Actions[:：]',
    ],
}


# =============================================================================
# Core Functions
# =============================================================================

def normalize_value(value: str) -> str:
    """Normalize a field value."""
    if not value:
        return ""
    # Remove markdown formatting
    value = re.sub(r'[*_#`]', '', value)
    # Collapse whitespace
    value = ' '.join(value.split())
    # Truncate if too long
    return value[:500].strip()


def is_placeholder(value: str) -> bool:
    """Check if value is a placeholder."""
    if not value:
        return True
    return value.lower().strip() in PLACEHOLDER_VALUES


def extract_field_value(content: str, field_name: str) -> Tuple[str, str, str]:
    """
    Extract a field value from markdown content.
    
    Returns: (status, raw_value, normalized_value)
    Status can be: 'valid', 'empty', 'missing'
    """
    if not content:
        return "missing", "", ""
    
    lines = content.split("\n")
    patterns = FIELD_PATTERNS.get(field_name, [])
    
    if not patterns:
        # Generic pattern
        patterns = [
            re.compile(rf'^##\s+{field_name}', re.IGNORECASE),
            re.compile(rf'^\*\*{field_name}\*\*[:：]?', re.IGNORECASE),
            re.compile(rf'^{field_name}[:：]', re.IGNORECASE),
        ]
    
    # Find the field
    field_line_idx = -1
    
    for i, line in enumerate(lines):
        for pattern in patterns:
            if isinstance(pattern, str):
                pattern = re.compile(pattern, re.IGNORECASE)
            if pattern.search(line):
                field_line_idx = i
                break
        if field_line_idx >= 0:
            break
    
    if field_line_idx < 0:
        return "missing", "", ""
    
    # Extract value
    raw_value = ""
    line = lines[field_line_idx]
    
    # For ## headers, value starts on next line
    if line.strip().startswith("##"):
        # Collect content until next ## or end
        value_lines = []
        for j in range(field_line_idx + 1, len(lines)):
            next_line = lines[j].strip()
            if next_line.startswith("##"):
                break
            # Skip empty lines at the start
            if not value_lines and not next_line:
                continue
            value_lines.append(lines[j])
        raw_value = "\n".join(value_lines).strip()
    else:
        # Value might be on same line after :
        for sep in [":", "："]:
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) > 1:
                    raw_value = parts[1].strip()
                    break
    
    # Normalize
    normalized = normalize_value(raw_value)
    
    # Determine status
    if not normalized or is_placeholder(normalized):
        return "empty", raw_value, ""
    
    return "valid", raw_value, normalized


def extract_all_fields(content: str, source_name: str = "unknown") -> Dict[str, FieldSource]:
    """Extract all tracked fields from markdown content."""
    results = {}
    
    for field_name in TRACKED_FIELDS:
        status, raw, normalized = extract_field_value(content, field_name)
        results[field_name] = FieldSource(
            status=status,
            value=normalized if status == "valid" else None,
            raw=raw[:100] if raw else None,
            source_file=source_name
        )
    
    return results


def resolve_field_conflicts(field_values: Dict[str, FieldSource]) -> FieldResolution:
    """
    Resolve conflicts for a single field across sources.
    
    Priority: Higher SOURCE_PRIORITY wins.
    """
    candidates = []
    
    for source, info in field_values.items():
        if info.status == "valid" and info.value:
            priority = SOURCE_PRIORITY.get(source, 0)
            candidates.append({
                "source": source,
                "value": info.value,
                "priority": priority
            })
    
    if not candidates:
        return FieldResolution(
            status="missing",
            value=None,
            reason="No valid values found"
        )
    
    # Sort by priority
    candidates.sort(key=lambda x: x["priority"], reverse=True)
    winner = candidates[0]
    
    # Check for conflicts
    conflicts = []
    for c in candidates[1:]:
        if c["value"] != winner["value"]:
            conflicts.append(ConflictInfo(
                source=c["source"],
                value=c["value"],
                priority=c["priority"]
            ))
    
    return FieldResolution(
        status="valid",
        value=winner["value"],
        chosen_source=winner["source"],
        reason=f"Highest priority source ({winner['source']}, priority={winner['priority']})",
        conflicts=conflicts if conflicts else None
    )


# =============================================================================
# Canonical-Ready Adapter Seam (Stub for Future)
# =============================================================================

class CanonicalAdapter:
    """
    Stub adapter for future canonical ledger integration.
    
    v0: Not connected to real ledger/run truth.
    Future: Will merge canonical state with materialized state.
    """
    
    def __init__(self, ledger_path: Optional[Path] = None):
        self.ledger_path = ledger_path
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to canonical ledger (stub)."""
        # v0: No-op
        self._connected = False
        return False
    
    def merge_with_canonical(self, state: MaterializedState) -> MaterializedState:
        """Merge materialized state with canonical state (stub)."""
        # v0: Return unchanged
        return state
    
    def is_connected(self) -> bool:
        return self._connected


# =============================================================================
# Main Materializer Class
# =============================================================================

class StateMaterializerV0:
    """
    Main class for materializing state from continuity sources.
    
    v0 Constraints:
    - Reads only SESSION-STATE.md and working-buffer.md
    - No handoff/capsule/summary/distill
    - No write-back
    - No second live state
    """
    
    def __init__(
        self,
        session_state_path: Optional[Path] = None,
        working_buffer_path: Optional[Path] = None,
        canonical_adapter: Optional[CanonicalAdapter] = None
    ):
        self.session_state_path = session_state_path
        self.working_buffer_path = working_buffer_path
        self.canonical_adapter = canonical_adapter or CanonicalAdapter()
    
    def materialize(
        self,
        session_state_content: Optional[str] = None,
        working_buffer_content: Optional[str] = None,
        branch: Optional[str] = None
    ) -> MaterializedState:
        """
        Materialize state from sources.
        
        Args:
            session_state_content: Content of SESSION-STATE.md (or read from path)
            working_buffer_content: Content of working-buffer.md (or read from path)
            branch: Current git branch (repo evidence)
        
        Returns:
            MaterializedState with resolved fields
        """
        state = MaterializedState(
            materialized_at=datetime.now().isoformat()
        )
        
        # Read from paths if content not provided
        if session_state_content is None and self.session_state_path:
            if self.session_state_path.exists():
                session_state_content = self.session_state_path.read_text()
        
        if working_buffer_content is None and self.working_buffer_path:
            if self.working_buffer_path.exists():
                working_buffer_content = self.working_buffer_path.read_text()
        
        # Track which sources were used
        if session_state_content:
            state.sources_checked.append("session_state_md")
        if working_buffer_content:
            state.sources_checked.append("working_buffer_md")
        if branch:
            state.sources_checked.append("repo_evidence")
        
        # Extract fields from each source
        all_field_values: Dict[str, Dict[str, FieldSource]] = {}
        
        if session_state_content:
            all_field_values["session_state_md"] = extract_all_fields(
                session_state_content, "SESSION-STATE.md"
            )
        
        if working_buffer_content:
            all_field_values["working_buffer_md"] = extract_all_fields(
                working_buffer_content, "working-buffer.md"
            )
        
        # Add repo evidence for branch
        if branch:
            all_field_values["repo_evidence"] = {
                "branch": FieldSource(
                    status="valid",
                    value=branch,
                    source_file="git"
                )
            }
        
        # Store field sources
        for source, fields in all_field_values.items():
            for field_name, field_source in fields.items():
                if field_name not in state.field_sources:
                    state.field_sources[field_name] = {}
                state.field_sources[field_name][source] = field_source
        
        # Resolve each field
        for field_name in TRACKED_FIELDS:
            field_values = {}
            for source, fields in all_field_values.items():
                if field_name in fields and fields[field_name].status == "valid":
                    field_values[source] = fields[field_name]
            
            if field_values:
                state.field_resolutions[field_name] = resolve_field_conflicts(field_values)
            else:
                state.field_resolutions[field_name] = FieldResolution(
                    status="missing",
                    value=None
                )
        
        # Populate top-level fields from resolutions
        state.objective = state.field_resolutions.get("objective", FieldResolution(status="missing")).value
        state.phase = state.field_resolutions.get("phase", FieldResolution(status="missing")).value
        state.branch = state.field_resolutions.get("branch", FieldResolution(status="missing")).value
        state.blocker = state.field_resolutions.get("blocker", FieldResolution(status="missing")).value
        state.next_step = state.field_resolutions.get("next_step", FieldResolution(status="missing")).value
        state.next_actions = self._parse_next_actions(
            state.field_resolutions.get("next_actions", FieldResolution(status="missing")).value
        )
        
        # Check for uncertainty (critical fields missing)
        # Only objective is truly critical; next_step is important but not required
        critical_fields = ["objective"]
        for field_name in critical_fields:
            resolution = state.field_resolutions.get(field_name)
            if resolution and resolution.status == "missing":
                state.uncertainty_flag = True
                break
        
        # Attempt canonical merge (stub in v0)
        if self.canonical_adapter and self.canonical_adapter.is_connected():
            state = self.canonical_adapter.merge_with_canonical(state)
        
        return state
    
    def _parse_next_actions(self, value: Optional[str]) -> Optional[List[str]]:
        """Parse next_actions from string or list format."""
        if not value:
            return None
        
        # If it's already a list, return it
        if isinstance(value, list):
            return value
        
        # Parse from string - look for bullet points or numbered items
        lines = value.strip().split("\n")
        actions = []
        
        for line in lines:
            line = line.strip()
            # Match "- action" or "1. action" patterns
            if line.startswith("- ") or line.startswith("* "):
                actions.append(line[2:].strip())
            elif re.match(r'^\d+\.\s+', line):
                actions.append(re.sub(r'^\d+\.\s+', '', line).strip())
            elif line and not line.startswith("#"):
                actions.append(line)
        
        return actions if actions else None


# =============================================================================
# Convenience Functions
# =============================================================================

def materialize_state(
    workspace_path: Optional[Path] = None,
    session_state_content: Optional[str] = None,
    working_buffer_content: Optional[str] = None,
    branch: Optional[str] = None
) -> MaterializedState:
    """
    Convenience function to materialize state.
    
    Args:
        workspace_path: Path to workspace (default: /home/moonlight/.openclaw/workspace)
        session_state_content: Override SESSION-STATE.md content
        working_buffer_content: Override working-buffer.md content
        branch: Override git branch
    
    Returns:
        MaterializedState
    """
    workspace = workspace_path or Path("/home/moonlight/.openclaw/workspace")
    
    materializer = StateMaterializerV0(
        session_state_path=workspace / "SESSION-STATE.md",
        working_buffer_path=workspace / "working-buffer.md"
    )
    
    return materializer.materialize(
        session_state_content=session_state_content,
        working_buffer_content=working_buffer_content,
        branch=branch
    )

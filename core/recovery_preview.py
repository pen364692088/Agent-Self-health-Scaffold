"""
Recovery Preview - Materialized-State-Driven Recovery Preview (Shadow Mode)

Provides a shadow recovery preview using MaterializedState and CanonicalAdapter.
Does NOT replace the main recovery chain.

v0 Constraints:
- Shadow mode only - does not replace main recovery chain
- Does NOT trigger real recovery actions
- Conflict fields are NOT silently used
- Missing blocker triggers explicit warning
- MaterializedState is NOT the recovery authority

Output:
- Recovery preview for comparison
- Dual-run compare with existing recovery flow
- Provenance-tracked differences
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class RecoveryField:
    """A field in the recovery preview."""
    name: str
    value: Optional[Any]
    source: str
    status: str  # 'valid', 'empty', 'missing', 'conflict'
    conflict_info: Optional[Dict[str, Any]] = None


@dataclass
class RecoveryPreview:
    """Recovery preview from MaterializedState + CanonicalAdapter."""
    session_id: Optional[str]
    generated_at: str
    phase: Optional[str]
    next_step: Optional[str]
    blocker: Optional[str]
    objective: Optional[str]
    fields: Dict[str, RecoveryField] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    uncertainty_flag: bool = False
    should_recover: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "generated_at": self.generated_at,
            "phase": self.phase,
            "next_step": self.next_step,
            "blocker": self.blocker,
            "objective": self.objective,
            "fields": {
                name: {
                    "value": f.value,
                    "source": f.source,
                    "status": f.status,
                    "conflict_info": f.conflict_info
                }
                for name, f in self.fields.items()
            },
            "warnings": self.warnings,
            "conflicts": self.conflicts,
            "provenance": self.provenance,
            "uncertainty_flag": self.uncertainty_flag,
            "should_recover": self.should_recover
        }


@dataclass
class RecoveryCompare:
    """Comparison between main recovery and shadow preview."""
    generated_at: str
    main_recovery: Dict[str, Any]
    shadow_preview: Dict[str, Any]
    field_differences: Dict[str, Dict[str, Any]]
    phase_comparison: Dict[str, Any]
    next_step_comparison: Dict[str, Any]
    blocker_comparison: Dict[str, Any]
    warnings_comparison: Dict[str, Any]
    provenance_comparison: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "main_recovery": self.main_recovery,
            "shadow_preview": self.shadow_preview,
            "field_differences": self.field_differences,
            "phase_comparison": self.phase_comparison,
            "next_step_comparison": self.next_step_comparison,
            "blocker_comparison": self.blocker_comparison,
            "warnings_comparison": self.warnings_comparison,
            "provenance_comparison": self.provenance_comparison,
            "recommendations": self.recommendations
        }


# =============================================================================
# Recovery Preview Generator
# =============================================================================

class RecoveryPreviewGenerator:
    """
    Generate recovery preview from MaterializedState and CanonicalAdapter.
    
    Shadow mode only - does NOT trigger real recovery actions.
    """
    
    def __init__(
        self,
        warn_on_missing_blocker: bool = True,
        warn_on_uncertainty: bool = True,
        include_conflict_details: bool = True
    ):
        self.warn_on_missing_blocker = warn_on_missing_blocker
        self.warn_on_uncertainty = warn_on_uncertainty
        self.include_conflict_details = include_conflict_details
    
    def generate(
        self,
        materialized_state: Dict[str, Any],
        canonical_state: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> RecoveryPreview:
        """
        Generate recovery preview.
        
        Args:
            materialized_state: Output from MaterializedState.to_dict()
            canonical_state: Optional output from CanonicalAdapter.extract_canonical_fields()
            session_id: Optional session identifier
        
        Returns:
            RecoveryPreview with recovery-relevant fields
        """
        warnings = []
        conflicts = []
        provenance = {}
        
        # Extract core fields from materialized state
        objective = materialized_state.get("objective")
        phase = materialized_state.get("phase")
        next_step = materialized_state.get("next_step")
        blocker = materialized_state.get("blocker")
        uncertainty_flag = materialized_state.get("uncertainty_flag", False)
        
        # Track sources
        sources_checked = materialized_state.get("sources_checked", [])
        provenance["materialized_sources"] = sources_checked
        
        # Check for missing blocker
        if self.warn_on_missing_blocker and blocker is None:
            warnings.append("BLOCKER_MISSING: No blocker information available in materialized state")
        
        # Check for uncertainty
        if self.warn_on_uncertainty and uncertainty_flag:
            warnings.append("UNCERTAINTY_DETECTED: Critical fields missing in materialized state")
        
        # Build fields dict
        fields: Dict[str, RecoveryField] = {}
        
        # Objective field
        fields["objective"] = RecoveryField(
            name="objective",
            value=objective,
            source=self._get_field_source(materialized_state, "objective"),
            status=self._get_field_status(objective)
        )
        
        # Phase field
        fields["phase"] = RecoveryField(
            name="phase",
            value=phase,
            source=self._get_field_source(materialized_state, "phase"),
            status=self._get_field_status(phase)
        )
        
        # Next step field
        fields["next_step"] = RecoveryField(
            name="next_step",
            value=next_step,
            source=self._get_field_source(materialized_state, "next_step"),
            status=self._get_field_status(next_step)
        )
        
        # Blocker field
        fields["blocker"] = RecoveryField(
            name="blocker",
            value=blocker,
            source=self._get_field_source(materialized_state, "blocker"),
            status=self._get_field_status(blocker)
        )
        
        # Merge with canonical state if provided
        if canonical_state:
            canonical_provenance = {}
            
            for field_name, canonical_field in canonical_state.items():
                if isinstance(canonical_field, dict):
                    canonical_value = canonical_field.get("value")
                    canonical_source = canonical_field.get("source", "canonical")
                    
                    # Check for conflicts
                    if field_name in fields:
                        bridge_value = fields[field_name].value
                        
                        if bridge_value and canonical_value and bridge_value != canonical_value:
                            # Conflict detected
                            conflict = {
                                "field": field_name,
                                "bridge_value": bridge_value,
                                "bridge_source": fields[field_name].source,
                                "canonical_value": canonical_value,
                                "canonical_source": canonical_source
                            }
                            conflicts.append(conflict)
                            
                            # Update field status
                            fields[field_name].status = "conflict"
                            fields[field_name].conflict_info = conflict
                            
                            if self.include_conflict_details:
                                provenance[f"{field_name}_conflict"] = conflict
                    
                    canonical_provenance[field_name] = {
                        "value": canonical_value,
                        "source": canonical_source
                    }
            
            provenance["canonical_sources"] = canonical_provenance
        
        # Determine if recovery should happen
        should_recover = self._should_trigger_recovery(fields, uncertainty_flag)
        
        # Add recovery recommendation to warnings
        if should_recover:
            if uncertainty_flag:
                warnings.append("RECOVERY_RECOMMENDED: Uncertainty flag detected, recovery may be needed")
            elif not objective:
                warnings.append("RECOVERY_RECOMMENDED: Objective missing, recovery may be needed")
        
        return RecoveryPreview(
            session_id=session_id,
            generated_at=datetime.now().isoformat(),
            phase=phase,
            next_step=next_step,
            blocker=blocker,
            objective=objective,
            fields=fields,
            warnings=warnings,
            conflicts=conflicts,
            provenance=provenance,
            uncertainty_flag=uncertainty_flag,
            should_recover=should_recover
        )
    
    def _get_field_source(self, state: Dict[str, Any], field_name: str) -> str:
        """Get the source for a field."""
        resolutions = state.get("field_resolutions", {})
        if field_name in resolutions:
            return resolutions[field_name].get("chosen_source", "unknown")
        return "unknown"
    
    def _get_field_status(self, value: Any) -> str:
        """Get status for a field value."""
        if value is None:
            return "missing"
        if isinstance(value, str) and not value.strip():
            return "empty"
        return "valid"
    
    def _should_trigger_recovery(self, fields: Dict[str, RecoveryField], uncertainty_flag: bool) -> bool:
        """Determine if recovery should be triggered."""
        if uncertainty_flag:
            return True
        if fields.get("objective") and fields["objective"].status == "missing":
            return True
        if fields.get("phase") and fields["phase"].status == "missing":
            return True
        return False


# =============================================================================
# Recovery Compare
# =============================================================================

class RecoveryCompareGenerator:
    """
    Compare main recovery output with shadow preview.
    """
    
    def compare(
        self,
        main_recovery: Dict[str, Any],
        shadow_preview: RecoveryPreview
    ) -> RecoveryCompare:
        """
        Compare main recovery output with shadow preview.
        
        Args:
            main_recovery: Output from session-start-recovery --recover --json
            shadow_preview: RecoveryPreview from RecoveryPreviewGenerator
        
        Returns:
            RecoveryCompare with detailed comparison
        """
        shadow_dict = shadow_preview.to_dict()
        
        # Field differences
        field_differences = {}
        
        # Compare each key field
        key_fields = ["objective", "phase", "next_step", "blocker"]
        
        for field_name in key_fields:
            main_value = self._extract_main_value(main_recovery, field_name)
            shadow_value = shadow_dict.get(field_name)
            
            if main_value != shadow_value:
                field_differences[field_name] = {
                    "main_value": main_value,
                    "shadow_value": shadow_value,
                    "match": False
                }
            else:
                field_differences[field_name] = {
                    "main_value": main_value,
                    "shadow_value": shadow_value,
                    "match": True
                }
        
        # Phase comparison
        phase_comparison = {
            "main_phase": self._extract_main_value(main_recovery, "phase"),
            "shadow_phase": shadow_preview.phase,
            "match": self._extract_main_value(main_recovery, "phase") == shadow_preview.phase
        }
        
        # Next step comparison
        next_step_comparison = {
            "main_next_step": self._extract_main_value(main_recovery, "next_step"),
            "shadow_next_step": shadow_preview.next_step,
            "match": self._extract_main_value(main_recovery, "next_step") == shadow_preview.next_step
        }
        
        # Blocker comparison
        main_blocker = self._extract_main_value(main_recovery, "blocker")
        shadow_blocker = shadow_preview.blocker
        blocker_comparison = {
            "main_blocker": main_blocker,
            "shadow_blocker": shadow_blocker,
            "match": main_blocker == shadow_blocker,
            "main_has_blocker": main_blocker is not None,
            "shadow_has_blocker": shadow_blocker is not None
        }
        
        # Warnings comparison
        main_warnings = main_recovery.get("uncertainty_flag", False)
        shadow_warnings = shadow_preview.warnings
        warnings_comparison = {
            "main_uncertainty_flag": main_warnings,
            "shadow_warnings_count": len(shadow_warnings),
            "shadow_warnings": shadow_warnings
        }
        
        # Provenance comparison
        provenance_comparison = {
            "main_sources": main_recovery.get("sources", {}),
            "shadow_provenance": shadow_dict.get("provenance", {})
        }
        
        # Generate recommendations
        recommendations = []
        
        # Check for differences
        mismatches = [f for f, d in field_differences.items() if not d["match"]]
        if mismatches:
            recommendations.append(
                f"FIELD_MISMATCH: {', '.join(mismatches)} differ between main and shadow"
            )
        
        # Check blocker
        if blocker_comparison["main_has_blocker"] != blocker_comparison["shadow_has_blocker"]:
            recommendations.append(
                "BLOCKER_DISCREPANCY: Blocker presence differs between main and shadow"
            )
        
        # Check warnings
        if shadow_warnings:
            for w in shadow_warnings:
                if "BLOCKER_MISSING" in w:
                    recommendations.append(
                        "WARNING: Blocker missing in shadow preview - review before using"
                    )
                elif "UNCERTAINTY" in w:
                    recommendations.append(
                        "WARNING: Uncertainty detected in shadow preview - review before using"
                    )
        
        # Check conflicts
        if shadow_preview.conflicts:
            recommendations.append(
                f"INFO: {len(shadow_preview.conflicts)} field conflicts detected in shadow preview"
            )
        
        return RecoveryCompare(
            generated_at=datetime.now().isoformat(),
            main_recovery=main_recovery,
            shadow_preview=shadow_dict,
            field_differences=field_differences,
            phase_comparison=phase_comparison,
            next_step_comparison=next_step_comparison,
            blocker_comparison=blocker_comparison,
            warnings_comparison=warnings_comparison,
            provenance_comparison=provenance_comparison,
            recommendations=recommendations
        )
    
    def _extract_main_value(self, main_recovery: Dict[str, Any], field_name: str) -> Optional[Any]:
        """Extract value from main recovery output."""
        # Try field_resolution first
        field_resolution = main_recovery.get("field_resolution", {})
        if field_name in field_resolution:
            return field_resolution[field_name].get("value")
        
        # Try top-level
        return main_recovery.get(field_name)


# =============================================================================
# Convenience Functions
# =============================================================================

def create_recovery_preview(
    materialized_state: Dict[str, Any],
    canonical_state: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> RecoveryPreview:
    """
    Create a recovery preview.
    
    Args:
        materialized_state: Output from MaterializedState.to_dict()
        canonical_state: Optional output from CanonicalAdapter.extract_canonical_fields()
        session_id: Optional session identifier
    
    Returns:
        RecoveryPreview
    """
    generator = RecoveryPreviewGenerator()
    return generator.generate(materialized_state, canonical_state, session_id)


def create_recovery_compare(
    main_recovery: Dict[str, Any],
    materialized_state: Dict[str, Any],
    canonical_state: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> RecoveryCompare:
    """
    Create a recovery comparison.
    
    Args:
        main_recovery: Output from session-start-recovery --recover --json
        materialized_state: Output from MaterializedState.to_dict()
        canonical_state: Optional output from CanonicalAdapter.extract_canonical_fields()
        session_id: Optional session identifier
    
    Returns:
        RecoveryCompare
    """
    preview = create_recovery_preview(materialized_state, canonical_state, session_id)
    comparator = RecoveryCompareGenerator()
    return comparator.compare(main_recovery, preview)

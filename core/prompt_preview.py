"""
Prompt Preview - Materialized-State-Driven Prompt Assembly (Shadow Mode)

Provides a shadow prompt assembly using MaterializedState instead of active_state.json.
Does NOT replace the main prompt-assemble chain.

v0 Constraints:
- Shadow mode only - does not replace main prompt chain
- Conflict fields are NOT silently included in prompt
- Missing blocker triggers explicit warning
- Does not become authority for prompt generation

Output:
- Prompt preview for comparison
- Dual-run compare report
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
class PromptLayer:
    """A layer in the prompt assembly."""
    name: str
    tokens: int
    components: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptPreview:
    """Assembled prompt preview from MaterializedState."""
    session_id: Optional[str]
    generated_at: str
    prompt_tokens: int
    max_tokens: int
    layers: Dict[str, PromptLayer] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    fallbacks: List[Dict[str, Any]] = field(default_factory=list)
    uncertainty_flag: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "generated_at": self.generated_at,
            "prompt_tokens": self.prompt_tokens,
            "max_tokens": self.max_tokens,
            "layers": {
                name: {
                    "tokens": layer.tokens,
                    "components": layer.components,
                    "data": layer.data
                }
                for name, layer in self.layers.items()
            },
            "warnings": self.warnings,
            "conflicts": self.conflicts,
            "fallbacks": self.fallbacks,
            "uncertainty_flag": self.uncertainty_flag
        }


@dataclass
class DualRunCompare:
    """Comparison between main chain and shadow preview."""
    generated_at: str
    main_chain: Dict[str, Any]
    shadow_preview: Dict[str, Any]
    comparison: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "main_chain": self.main_chain,
            "shadow_preview": self.shadow_preview,
            "comparison": self.comparison,
            "quality_metrics": self.quality_metrics,
            "recommendations": self.recommendations
        }


# =============================================================================
# Token Estimation
# =============================================================================

def estimate_tokens(text: str) -> int:
    """Estimate token count: 4 chars ≈ 1 token."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_json_tokens(data: Any) -> int:
    """Estimate tokens from JSON-serializable data."""
    try:
        text = json.dumps(data, ensure_ascii=False)
        return estimate_tokens(text)
    except Exception:
        return 0


# =============================================================================
# Prompt Assembly from MaterializedState
# =============================================================================

class MaterializedStatePromptAssembler:
    """
    Assemble prompt preview from MaterializedState.
    
    Shadow mode only - does not replace main prompt chain.
    """
    
    def __init__(
        self,
        max_tokens: int = 100000,
        include_conflicts: bool = False,  # Default: do NOT include conflicts
        warn_on_missing_blocker: bool = True
    ):
        self.max_tokens = max_tokens
        self.include_conflicts = include_conflicts
        self.warn_on_missing_blocker = warn_on_missing_blocker
    
    def assemble(
        self,
        materialized_state: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> PromptPreview:
        """
        Assemble prompt preview from MaterializedState.
        
        Args:
            materialized_state: Output from MaterializedState.to_dict()
            session_id: Optional session identifier
        
        Returns:
            PromptPreview with assembled layers
        """
        warnings = []
        conflicts = []
        fallbacks = []
        
        # Extract fields from materialized state
        objective = materialized_state.get("objective")
        phase = materialized_state.get("phase")
        branch = materialized_state.get("branch")
        blocker = materialized_state.get("blocker")
        next_step = materialized_state.get("next_step")
        next_actions = materialized_state.get("next_actions")
        uncertainty_flag = materialized_state.get("uncertainty_flag", False)
        
        # Check for missing blocker (explicit warning)
        if self.warn_on_missing_blocker and blocker is None:
            warnings.append("BLOCKER_MISSING: No blocker information available")
        
        # Check for uncertainty
        if uncertainty_flag:
            warnings.append("UNCERTAINTY_DETECTED: Critical fields missing in materialized state")
        
        # Extract conflicts from field_resolutions
        field_resolutions = materialized_state.get("field_resolutions", {})
        for field_name, resolution in field_resolutions.items():
            if isinstance(resolution, dict) and resolution.get("conflicts"):
                for conflict in resolution["conflicts"]:
                    conflicts.append({
                        "field": field_name,
                        "bridge_value": resolution.get("value"),
                        "conflict_value": conflict.get("value"),
                        "conflict_source": conflict.get("source"),
                        "included_in_prompt": self.include_conflicts  # Default False
                    })
        
        # Build layers
        layers = {}
        
        # 1. Resident layer (task context)
        resident_components = []
        resident_data = {}
        resident_tokens = 0
        
        if objective:
            resident_data["objective"] = objective
            resident_components.append("objective")
            resident_tokens += estimate_tokens(objective)
        
        if phase:
            resident_data["phase"] = phase
            resident_components.append("phase")
            resident_tokens += estimate_tokens(phase)
        
        if branch:
            resident_data["branch"] = branch
            resident_components.append("branch")
            resident_tokens += estimate_tokens(branch)
        
        # Blocker handling (with explicit warning)
        if blocker:
            resident_data["blocker"] = blocker
            resident_components.append("blocker")
            resident_tokens += estimate_tokens(blocker)
        elif self.include_conflicts:
            # Only include if explicitly requested
            pass
        
        layers["resident"] = PromptLayer(
            name="resident",
            tokens=resident_tokens,
            components=resident_components,
            data=resident_data
        )
        
        # 2. Action layer (next steps)
        action_components = []
        action_data = {}
        action_tokens = 0
        
        if next_step:
            action_data["next_step"] = next_step
            action_components.append("next_step")
            action_tokens += estimate_tokens(next_step)
        
        if next_actions:
            action_data["next_actions"] = next_actions
            action_components.append("next_actions")
            action_tokens += estimate_json_tokens(next_actions)
        
        layers["action"] = PromptLayer(
            name="action",
            tokens=action_tokens,
            components=action_components,
            data=action_data
        )
        
        # 3. Metadata layer (provenance)
        metadata_components = []
        metadata_data = {}
        metadata_tokens = 0
        
        sources_checked = materialized_state.get("sources_checked", [])
        if sources_checked:
            metadata_data["sources_checked"] = sources_checked
            metadata_components.append("sources_checked")
            metadata_tokens += estimate_json_tokens(sources_checked)
        
        field_sources = materialized_state.get("field_sources", {})
        if field_sources:
            # Only include source names, not full data
            source_summary = {}
            for field_name, sources in field_sources.items():
                for source_name, source_info in sources.items():
                    if isinstance(source_info, dict) and source_info.get("status") == "valid":
                        source_summary[field_name] = source_name
                        break
            
            if source_summary:
                metadata_data["field_sources_summary"] = source_summary
                metadata_components.append("field_sources_summary")
                metadata_tokens += estimate_json_tokens(source_summary)
        
        layers["metadata"] = PromptLayer(
            name="metadata",
            tokens=metadata_tokens,
            components=metadata_components,
            data=metadata_data
        )
        
        # Calculate total tokens
        total_tokens = sum(layer.tokens for layer in layers.values())
        
        return PromptPreview(
            session_id=session_id,
            generated_at=datetime.now().isoformat(),
            prompt_tokens=total_tokens,
            max_tokens=self.max_tokens,
            layers=layers,
            warnings=warnings,
            conflicts=conflicts,
            fallbacks=fallbacks,
            uncertainty_flag=uncertainty_flag
        )


# =============================================================================
# Dual-Run Comparison
# =============================================================================

class DualRunComparator:
    """
    Compare main chain prompt-assemble output with shadow preview.
    """
    
    def compare(
        self,
        main_chain_output: Dict[str, Any],
        shadow_preview: PromptPreview
    ) -> DualRunCompare:
        """
        Compare main chain output with shadow preview.
        
        Args:
            main_chain_output: Output from prompt-assemble
            shadow_preview: PromptPreview from MaterializedState
        
        Returns:
            DualRunCompare with detailed comparison
        """
        shadow_dict = shadow_preview.to_dict()
        
        comparison = {
            "token_usage": {
                "main_chain_tokens": main_chain_output.get("prompt_tokens", 0),
                "shadow_preview_tokens": shadow_preview.prompt_tokens,
                "difference": main_chain_output.get("prompt_tokens", 0) - shadow_preview.prompt_tokens
            },
            "layer_coverage": {
                "main_chain_layers": list(main_chain_output.get("layers", {}).keys()),
                "shadow_preview_layers": list(shadow_preview.layers.keys()),
                "common_layers": list(
                    set(main_chain_output.get("layers", {}).keys()) &
                    set(shadow_preview.layers.keys())
                )
            },
            "input_sources": {
                "main_chain": "active_state.json + raw.jsonl",
                "shadow_preview": "MaterializedState (SESSION-STATE.md + working-buffer.md)"
            },
            "features": {
                "main_chain_compression": main_chain_output.get("compression_applied", False),
                "shadow_preview_warnings": len(shadow_preview.warnings),
                "shadow_preview_conflicts": len(shadow_preview.conflicts)
            }
        }
        
        # Quality metrics
        quality_metrics = {
            "completeness": self._assess_completeness(shadow_preview),
            "consistency": self._assess_consistency(main_chain_output, shadow_dict),
            "observability": self._assess_observability(shadow_preview),
            "warnings_present": len(shadow_preview.warnings) > 0,
            "conflicts_detected": len(shadow_preview.conflicts) > 0,
            "uncertainty_flagged": shadow_preview.uncertainty_flag
        }
        
        # Recommendations
        recommendations = []
        
        if shadow_preview.uncertainty_flag:
            recommendations.append(
                "CRITICAL: Uncertainty flag detected. Review materialized state for missing fields."
            )
        
        if shadow_preview.warnings:
            recommendations.append(
                f"WARNING: {len(shadow_preview.warnings)} warnings detected. Review before using shadow preview."
            )
        
        if shadow_preview.conflicts:
            recommendations.append(
                f"INFO: {len(shadow_preview.conflicts)} field conflicts detected. "
                "Conflicts are NOT included in prompt by default."
            )
        
        # Compare objective presence
        main_objective = main_chain_output.get("layers", {}).get("resident", {}).get("data", {}).get("task_goal")
        shadow_objective = shadow_dict.get("layers", {}).get("resident", {}).get("data", {}).get("objective")
        
        if main_objective and shadow_objective:
            if main_objective != shadow_objective:
                recommendations.append(
                    "DIVERGENCE: Objective/task_goal differs between main chain and shadow preview."
                )
        
        return DualRunCompare(
            generated_at=datetime.now().isoformat(),
            main_chain=main_chain_output,
            shadow_preview=shadow_dict,
            comparison=comparison,
            quality_metrics=quality_metrics,
            recommendations=recommendations
        )
    
    def _assess_completeness(self, preview: PromptPreview) -> Dict[str, Any]:
        """Assess completeness of shadow preview."""
        required_fields = ["objective", "phase", "next_step"]
        present = []
        missing = []
        
        resident_data = preview.layers.get("resident", PromptLayer(name="resident", tokens=0)).data
        
        for field in required_fields:
            if resident_data.get(field):
                present.append(field)
            else:
                missing.append(field)
        
        return {
            "score": len(present) / len(required_fields) if required_fields else 0,
            "present": present,
            "missing": missing
        }
    
    def _assess_consistency(
        self,
        main_chain: Dict[str, Any],
        shadow_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess consistency between main chain and shadow."""
        main_tokens = main_chain.get("prompt_tokens", 0)
        shadow_tokens = shadow_dict.get("prompt_tokens", 0)
        
        # Allow 20% variance
        ratio = shadow_tokens / main_tokens if main_tokens > 0 else 0
        consistent = 0.8 <= ratio <= 1.2 if main_tokens > 0 else True
        
        return {
            "token_ratio": round(ratio, 2),
            "consistent": consistent,
            "variance_percent": round(abs(ratio - 1) * 100, 1)
        }
    
    def _assess_observability(self, preview: PromptPreview) -> Dict[str, Any]:
        """Assess observability features of shadow preview."""
        return {
            "has_warnings": len(preview.warnings) > 0,
            "has_conflicts": len(preview.conflicts) > 0,
            "has_fallbacks": len(preview.fallbacks) > 0,
            "has_uncertainty_flag": preview.uncertainty_flag,
            "sources_tracked": "metadata" in preview.layers
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_shadow_prompt_preview(
    materialized_state: Dict[str, Any],
    session_id: Optional[str] = None,
    max_tokens: int = 100000
) -> PromptPreview:
    """
    Create a shadow prompt preview from MaterializedState.
    
    Args:
        materialized_state: Output from MaterializedState.to_dict()
        session_id: Optional session identifier
        max_tokens: Maximum tokens for prompt
    
    Returns:
        PromptPreview
    """
    assembler = MaterializedStatePromptAssembler(max_tokens=max_tokens)
    return assembler.assemble(materialized_state, session_id)


def create_dual_run_compare(
    main_chain_output: Dict[str, Any],
    materialized_state: Dict[str, Any],
    session_id: Optional[str] = None
) -> DualRunCompare:
    """
    Create a dual-run comparison.
    
    Args:
        main_chain_output: Output from prompt-assemble
        materialized_state: Output from MaterializedState.to_dict()
        session_id: Optional session identifier
    
    Returns:
        DualRunCompare
    """
    preview = create_shadow_prompt_preview(materialized_state, session_id)
    comparator = DualRunComparator()
    return comparator.compare(main_chain_output, preview)

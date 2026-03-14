"""
Prompt Pilot Runner - Executes shadow prompt assembly in pilot mode.

This module provides the integration point between the prompt assembly
system and the pilot framework. It handles:
- Checking if pilot is enabled for the task type
- Running shadow prompt assembly
- Comparing with main chain
- Logging metrics
- Fallback to main chain on error

CONSTRAINTS:
- Does NOT replace main chain as authority
- Does NOT modify live state
- Does NOT enable recovery live
- Fallback to main chain on any error
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# Add workspace to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.prompt_preview import MaterializedStatePromptAssembler
from core.materialized_state_v0 import MaterializedState


@dataclass
class PilotResult:
    """Result from a pilot run."""
    success: bool
    used_shadow: bool
    match_rate: float
    conflict_count: int
    missing_count: int
    token_overhead: float
    fallback: bool
    error: Optional[str] = None
    shadow_prompt: Optional[str] = None
    main_prompt: Optional[str] = None


class PromptPilotRunner:
    """
    Runner for the prompt pilot system.
    
    Integrates shadow prompt assembly with the main chain,
    following all safety constraints.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (
            Path(__file__).parent.parent / "config" / "prompt_pilot.json"
        )
        self.metrics_path = (
            Path(__file__).parent.parent / "artifacts" / "prompt_pilot" / "metrics.jsonl"
        )
    
    def load_config(self) -> Dict[str, Any]:
        """Load pilot configuration."""
        if not self.config_path.exists():
            return {
                "pilot_enabled": False,
                "pilot_mode": "shadow",
                "allowed_events": [],
                "authority_chain": {"prompt": "main_chain"},
                "fallback_on_error": True,
                "stop_conditions": {}
            }
        
        with open(self.config_path) as f:
            return json.load(f)
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save pilot configuration."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def is_enabled(self, task_type: str) -> bool:
        """Check if pilot is enabled for this task type."""
        config = self.load_config()
        
        if not config.get("pilot_enabled"):
            return False
        
        allowed = config.get("allowed_events", [])
        blocked = config.get("blocked_events", [])
        
        if task_type in blocked:
            return False
        
        return task_type in allowed
    
    def get_mode(self) -> str:
        """Get current pilot mode."""
        config = self.load_config()
        return config.get("pilot_mode", "shadow")
    
    def should_use_shadow(self, task_type: str) -> bool:
        """Determine if shadow should be used for this task."""
        if not self.is_enabled(task_type):
            return False
        
        mode = self.get_mode()
        
        # In shadow mode, we just log comparison
        # In pilot mode, we might use shadow output
        return mode in ("shadow", "pilot")
    
    def run_shadow_assembly(
        self,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Run shadow prompt assembly.
        
        Returns:
            Tuple of (prompt_text, metadata)
        """
        try:
            # Create MaterializedState
            m = MaterializedState()
            
            # Override with context if provided
            if context:
                if context.get('objective'):
                    m.objective = context['objective']
                if context.get('phase'):
                    m.phase = context['phase']
                if context.get('next_step'):
                    m.next_step = context['next_step']
                if context.get('blocker'):
                    m.blocker = context['blocker']
                if context.get('branch'):
                    m.branch = context['branch']
            
            state_dict = m.to_dict()
            
            # Assemble prompt
            assembler = MaterializedStatePromptAssembler()
            result = assembler.assemble(state_dict, session_id=session_id)
            
            # Build prompt text
            prompt_lines = []
            for layer_name, layer in result.layers.items():
                prompt_lines.append(f"## {layer_name.upper()}")
                for component in layer.components:
                    prompt_lines.append(str(component))
                if layer.data:
                    prompt_lines.append(json.dumps(layer.data, indent=2, ensure_ascii=False))
            
            prompt_text = "\n".join(prompt_lines)
            
            # Build metadata
            metadata = {
                "layers": list(result.layers.keys()),
                "conflicts": result.conflicts,
                "warnings": result.warnings,
                "prompt_tokens": result.prompt_tokens,
                "conflict_count": len(result.conflicts),
                "missing_count": len(result.warnings),
                "state_coverage": sum(1 for v in state_dict.values() if v is not None) / max(len(state_dict), 1)
            }
            
            return prompt_text, metadata
            
        except Exception as e:
            return None, {"error": str(e)}
    
    def calculate_match_rate(
        self,
        shadow_metadata: Dict[str, Any],
        main_metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate match rate between shadow and main."""
        if shadow_metadata.get("error"):
            return 0.0
        
        # If no main to compare, use coverage as proxy
        if not main_metadata:
            return shadow_metadata.get("state_coverage", 0.8)
        
        # Compare layers
        shadow_layers = set(shadow_metadata.get("layers", []))
        main_layers = set(main_metadata.get("layers", []))
        
        if not main_layers:
            return shadow_metadata.get("state_coverage", 0.8)
        
        overlap = len(shadow_layers & main_layers)
        return overlap / max(len(main_layers), 1)
    
    def log_metrics(self, result: PilotResult, task_type: str, session_id: str) -> None:
        """Log pilot metrics."""
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "prompt_pilot_call",
            "session_id": session_id,
            "task_type": task_type,
            "success": result.success,
            "used_shadow": result.used_shadow,
            "match_rate": result.match_rate,
            "conflict_count": result.conflict_count,
            "missing_count": result.missing_count,
            "token_overhead": result.token_overhead,
            "fallback": result.fallback,
            "error": result.error
        }
        
        with open(self.metrics_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        # Update config metrics
        config = self.load_config()
        metrics = config.get("metrics", {})
        
        total = metrics.get("total_calls", 0) + 1
        
        # Running average
        def update_avg(name: str, new_val: float) -> float:
            old_avg = metrics.get(name, 0.0)
            return (old_avg * (total - 1) + new_val) / total
        
        config["metrics"] = {
            "total_calls": total,
            "successful_calls": metrics.get("successful_calls", 0) + (1 if result.success else 0),
            "fallback_calls": metrics.get("fallback_calls", 0) + (1 if result.fallback else 0),
            "error_calls": metrics.get("error_calls", 0) + (1 if result.error else 0),
            "avg_match_rate": update_avg("avg_match_rate", result.match_rate),
            "avg_conflict_rate": update_avg("avg_conflict_rate", result.conflict_count / max(total, 1)),
            "avg_missing_rate": update_avg("avg_missing_rate", result.missing_count / max(total, 1)),
            "avg_token_overhead": update_avg("avg_token_overhead", result.token_overhead)
        }
        
        self.save_config(config)
    
    def check_stop_conditions(self) -> Optional[str]:
        """Check if any stop condition is violated."""
        config = self.load_config()
        metrics = config.get("metrics", {})
        stop = config.get("stop_conditions", {})
        
        # Need at least 10 calls to check stop conditions
        if metrics.get("total_calls", 0) < 10:
            return None
        
        if metrics.get("avg_conflict_rate", 0) > stop.get("max_conflict_rate", 0.05):
            return f"Conflict rate {metrics['avg_conflict_rate']:.1%} > {stop['max_conflict_rate']:.1%}"
        
        if metrics.get("avg_missing_rate", 0) > stop.get("max_missing_rate", 0.05):
            return f"Missing rate {metrics['avg_missing_rate']:.1%} > {stop['max_missing_rate']:.1%}"
        
        if metrics.get("avg_match_rate", 0) < stop.get("min_match_rate", 0.80):
            return f"Match rate {metrics['avg_match_rate']:.1%} < {stop['min_match_rate']:.1%}"
        
        if metrics.get("avg_token_overhead", 0) > stop.get("max_token_overhead", 0.30):
            return f"Token overhead {metrics['avg_token_overhead']:.1%} > {stop['max_token_overhead']:.1%}"
        
        return None
    
    def run(
        self,
        task_type: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        main_prompt: Optional[str] = None,
        main_metadata: Optional[Dict[str, Any]] = None
    ) -> PilotResult:
        """
        Run the pilot for a given task.
        
        Args:
            task_type: Type of task (e.g., "recovery_success")
            session_id: Session identifier
            context: Optional state context
            main_prompt: Main chain prompt (for comparison)
            main_metadata: Main chain metadata
        
        Returns:
            PilotResult with metrics and status
        """
        # Check if enabled for this task
        if not self.is_enabled(task_type):
            return PilotResult(
                success=True,
                used_shadow=False,
                match_rate=0.0,
                conflict_count=0,
                missing_count=0,
                token_overhead=0.0,
                fallback=False,
                error="Pilot not enabled for this task type"
            )
        
        # Check stop conditions
        stop_violation = self.check_stop_conditions()
        if stop_violation:
            # Auto-disable pilot
            config = self.load_config()
            config["pilot_enabled"] = False
            self.save_config(config)
            
            return PilotResult(
                success=False,
                used_shadow=False,
                match_rate=0.0,
                conflict_count=0,
                missing_count=0,
                token_overhead=0.0,
                fallback=True,
                error=f"Stop condition violated: {stop_violation}"
            )
        
        # Run shadow assembly
        shadow_prompt, shadow_metadata = self.run_shadow_assembly(session_id, context)
        
        # Check for errors
        if shadow_metadata.get("error"):
            result = PilotResult(
                success=False,
                used_shadow=False,
                match_rate=0.0,
                conflict_count=0,
                missing_count=0,
                token_overhead=0.0,
                fallback=True,
                error=shadow_metadata["error"]
            )
            self.log_metrics(result, task_type, session_id)
            return result
        
        # Calculate metrics
        match_rate = self.calculate_match_rate(shadow_metadata, main_metadata)
        conflict_count = shadow_metadata.get("conflict_count", 0)
        missing_count = shadow_metadata.get("missing_count", 0)
        token_overhead = 0.0  # Would need actual token counts
        
        # Determine if we should use shadow output
        mode = self.get_mode()
        used_shadow = mode == "pilot" and not conflict_count
        
        result = PilotResult(
            success=True,
            used_shadow=used_shadow,
            match_rate=match_rate,
            conflict_count=conflict_count,
            missing_count=missing_count,
            token_overhead=token_overhead,
            fallback=False,
            shadow_prompt=shadow_prompt,
            main_prompt=main_prompt
        )
        
        self.log_metrics(result, task_type, session_id)
        
        return result


# Convenience function
def run_pilot(
    task_type: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None
) -> PilotResult:
    """Run the pilot for a given task."""
    runner = PromptPilotRunner()
    return runner.run(task_type, session_id, context)

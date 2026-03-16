#!/usr/bin/env python3
"""
Mutation Gate

Purpose:
  Integrate Memory Preflight into mutation operations.
  Provides gate sequence for all write operations.

Usage:
  from runtime.mutation_gate import MutationGate
  
  gate = MutationGate()
  result = gate.execute(task_id, intent, mutation_func, target_repo)
  
Version: v1.0
Date: 2026-03-16
Status: MANDATORY_ENFORCEMENT
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass

# Add runtime to path
runtime_dir = os.path.dirname(os.path.abspath(__file__))
if runtime_dir not in sys.path:
    sys.path.insert(0, runtime_dir)

from memory_preflight import MemoryPreflight, Decision, PreflightResult


@dataclass
class GateResult:
    """Result of mutation gate execution"""
    passed: bool
    preflight_result: PreflightResult
    mutation_result: Optional[Any]
    evidence_path: str
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "preflight": self.preflight_result.to_dict(),
            "mutation_result": str(self.mutation_result) if self.mutation_result else None,
            "evidence_path": self.evidence_path
        }


class MutationGate:
    """
    Mutation Gate
    
    Enforces Memory Preflight for all mutation operations.
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        self.preflight = MemoryPreflight(registry_path)
        
        workspace = os.environ.get("OPENCLAW_WORKSPACE",
                                   os.path.expanduser("~/.openclaw/workspace"))
        self.gate_log_path = os.path.join(workspace, "artifacts/mutations/gate_log.jsonl")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.gate_log_path), exist_ok=True)
    
    def execute(self,
                task_id: str,
                intent: str,
                mutation_func: Callable[[], Any],
                target_repo: Optional[str] = None,
                action: Optional[str] = None,
                bypass_allowed: bool = False) -> GateResult:
        """
        Execute mutation through gate sequence.
        
        Args:
            task_id: Task identifier
            intent: Task intent/description
            mutation_func: Function to execute if gate passes
            target_repo: Target repository
            action: Intended action
            bypass_allowed: Whether bypass is allowed (default: False)
            
        Returns:
            GateResult with execution outcome
        """
        # Gate M1-M4: Preflight Check
        preflight_result = self.preflight.check(
            task_id=task_id,
            intent=intent,
            target_repo=target_repo,
            action=action
        )
        
        # Gate M5: Execute or Block
        if preflight_result.is_blocked():
            # BLOCK
            if not bypass_allowed:
                self._log_gate_execution(
                    task_id=task_id,
                    intent=intent,
                    preflight_result=preflight_result,
                    executed=False,
                    reason="blocked_by_preflight"
                )
                
                return GateResult(
                    passed=False,
                    preflight_result=preflight_result,
                    mutation_result=None,
                    evidence_path=preflight_result.evidence_path
                )
        
        # ALLOW - Execute mutation
        try:
            mutation_result = mutation_func()
            executed = True
        except Exception as e:
            mutation_result = f"ERROR: {str(e)}"
            executed = False
        
        # Log execution
        evidence_path = self._log_gate_execution(
            task_id=task_id,
            intent=intent,
            preflight_result=preflight_result,
            executed=executed,
            reason="executed" if executed else "execution_error"
        )
        
        return GateResult(
            passed=executed,
            preflight_result=preflight_result,
            mutation_result=mutation_result,
            evidence_path=evidence_path
        )
    
    def check_only(self,
                   task_id: str,
                   intent: str,
                   target_repo: Optional[str] = None,
                   action: Optional[str] = None) -> PreflightResult:
        """
        Execute preflight check without executing mutation.
        
        Use this to validate before actual execution.
        """
        return self.preflight.check(
            task_id=task_id,
            intent=intent,
            target_repo=target_repo,
            action=action
        )
    
    def _log_gate_execution(self,
                            task_id: str,
                            intent: str,
                            preflight_result: PreflightResult,
                            executed: bool,
                            reason: str) -> str:
        """Log gate execution to JSONL file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "intent": intent,
            "decision": preflight_result.decision.value,
            "object_name": preflight_result.object_name,
            "resolved_target": preflight_result.resolved_target,
            "write_policy": preflight_result.write_policy,
            "executed": executed,
            "reason": reason,
            "consulted_sources": preflight_result.consulted_sources
        }
        
        with open(self.gate_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
        
        return self.gate_log_path
    
    def get_block_message(self, result: GateResult) -> str:
        """Generate human-readable block message"""
        return self.preflight.get_block_message(result.preflight_result)


# =============================================================================
# Decorator for automatic gate enforcement
# =============================================================================

def mutation_gate(intents_keyword: str = None):
    """
    Decorator to enforce mutation gate on functions.
    
    Usage:
        @mutation_gate("update unified state")
        def update_unified_state(data):
            # mutation logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Extract task_id from kwargs or generate
            task_id = kwargs.get('task_id', f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Create gate
            gate = MutationGate()
            
            # Check intent
            intent = intents_keyword or func.__name__.replace('_', ' ')
            
            # Execute through gate
            result = gate.execute(
                task_id=task_id,
                intent=intent,
                mutation_func=lambda: func(*args, **kwargs)
            )
            
            if not result.passed:
                raise PermissionError(gate.get_block_message(result))
            
            return result.mutation_result
        
        return wrapper
    return decorator


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI interface for mutation_gate"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mutation Gate")
    parser.add_argument("--task-id", required=True, help="Task identifier")
    parser.add_argument("--intent", required=True, help="Task intent/description")
    parser.add_argument("--repo", help="Target repository")
    parser.add_argument("--action", help="Intended action")
    parser.add_argument("--check-only", action="store_true", help="Only check, don't execute")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    gate = MutationGate()
    
    if args.check_only:
        result = gate.check_only(
            task_id=args.task_id,
            intent=args.intent,
            target_repo=args.repo,
            action=args.action
        )
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            if result.is_allowed():
                print(f"✅ CHECK PASSED: {result.reason}")
                if result.resolved_target:
                    print(f"   Target: {result.resolved_target}")
            else:
                print(gate.preflight.get_block_message(result))
    else:
        # For CLI, we can't execute arbitrary functions
        print("Use --check-only for CLI validation")
        print("For execution, use the Python API")


if __name__ == "__main__":
    main()

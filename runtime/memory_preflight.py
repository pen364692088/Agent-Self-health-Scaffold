#!/usr/bin/env python3
"""
Memory Preflight for Mutation

Purpose:
  Execute mandatory preflight checks before any mutation operation.
  Ensures canonical target resolution and write policy compliance.

Usage:
  from runtime.memory_preflight import MemoryPreflight
  
  preflight = MemoryPreflight()
  result = preflight.check(task_id, intent, target_repo)
  
  if result.decision == "allow":
      # Proceed with mutation
  else:
      # Block and report

Version: v1.0
Date: 2026-03-16
Status: MANDATORY_ENFORCEMENT
"""

import json
import yaml
import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class Decision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    UNCLEAR = "unclear"


@dataclass
class PreflightResult:
    """Result of preflight check"""
    decision: Decision
    object_name: Optional[str]
    resolved_target: Optional[str]
    write_policy: Optional[str]
    reason: str
    consulted_sources: List[str]
    evidence_path: Optional[str]
    
    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "object_name": self.object_name,
            "resolved_target": self.resolved_target,
            "write_policy": self.write_policy,
            "reason": self.reason,
            "consulted_sources": self.consulted_sources,
            "evidence_path": self.evidence_path
        }
    
    def is_allowed(self) -> bool:
        return self.decision == Decision.ALLOW
    
    def is_blocked(self) -> bool:
        return self.decision == Decision.BLOCK


class CanonicalRegistry:
    """Canonical Object Registry loader and resolver"""
    
    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            workspace = os.environ.get("OPENCLAW_WORKSPACE", 
                                       os.path.expanduser("~/.openclaw/workspace"))
            registry_path = os.path.join(workspace, 
                                        "docs/memory/CANONICAL_OBJECT_REGISTRY.yaml")
        
        self.registry_path = registry_path
        self.registry = self._load_registry()
    
    def _load_registry(self) -> dict:
        """Load registry from YAML file"""
        if not os.path.exists(self.registry_path):
            return {"canonical_objects": {}, "write_policies": {}}
        
        with open(self.registry_path, 'r') as f:
            return yaml.safe_load(f) or {"canonical_objects": {}, "write_policies": {}}
    
    def get_object(self, object_name: str) -> Optional[dict]:
        """Get canonical object definition"""
        return self.registry.get("canonical_objects", {}).get(object_name)
    
    def resolve_target(self, object_name: str, target_repo: Optional[str] = None) -> Optional[str]:
        """
        Resolve canonical target path for object.
        
        Args:
            object_name: Canonical object name
            target_repo: Target repository (optional, uses first if not specified)
            
        Returns:
            Resolved path or None if not found
        """
        obj = self.get_object(object_name)
        if not obj:
            return None
        
        targets = obj.get("allowed_targets", [])
        if not targets:
            return None
        
        if target_repo:
            for t in targets:
                if t.get("repo") == target_repo:
                    return t.get("path")
            return None
        
        # Return first target if no repo specified
        return targets[0].get("path")
    
    def get_write_policy(self, object_name: str, target_repo: Optional[str] = None) -> Optional[str]:
        """Get write policy for object"""
        obj = self.get_object(object_name)
        if not obj:
            return None
        
        targets = obj.get("allowed_targets", [])
        if target_repo:
            for t in targets:
                if t.get("repo") == target_repo:
                    return t.get("write_policy")
        
        return targets[0].get("write_policy") if targets else None
    
    def get_forbidden_actions(self, object_name: str) -> List[str]:
        """Get forbidden actions for object"""
        obj = self.get_object(object_name)
        if not obj:
            return []
        return obj.get("forbidden_actions", [])
    
    def get_ambiguity_policy(self, object_name: str) -> str:
        """Get ambiguity policy for object"""
        obj = self.get_object(object_name)
        if not obj:
            return "block"  # Default to block
        return obj.get("ambiguity_policy", "block")


class IntentParser:
    """Parse task intent to identify canonical objects"""
    
    # Keywords that indicate canonical object operations
    CANONICAL_KEYWORDS = {
        "unified_program_state": [
            "统一进度账",
            "统一程序状态",
            "unified progress",
            "unified state",
            "program state",
            "PROGRAM_STATE"
        ],
        "unified_progress_ledger": [
            "进度账本",
            "progress ledger",
            "PROGRESS_LEDGER"
        ],
        "session_state": [
            "会话状态",
            "session state",
            "SESSION-STATE",
            "working buffer"
        ],
        "handoff_document": [
            "交接文档",
            "handoff",
            "HANDOFF"
        ],
        "canonical_index": [
            "唯一索引",
            "canonical index",
            "session index"
        ],
        "memory_distillation": [
            "记忆蒸馏",
            "memory distillation",
            "distilled memory"
        ]
    }
    
    def parse(self, intent: str) -> Optional[str]:
        """
        Parse intent to identify canonical object.
        
        Args:
            intent: Task intent/description
            
        Returns:
            Canonical object name or None
        """
        if not intent:
            return None
        
        intent_lower = intent.lower()
        
        for object_name, keywords in self.CANONICAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in intent_lower:
                    return object_name
        
        return None
    
    def infer_action(self, intent: str) -> str:
        """
        Infer intended action from intent.
        
        Args:
            intent: Task intent/description
            
        Returns:
            Action type: create, modify, update, delete
        """
        if not intent:
            return "unknown"
        
        intent_lower = intent.lower()
        
        if any(kw in intent_lower for kw in ["create", "新建", "创建"]):
            return "create"
        if any(kw in intent_lower for kw in ["delete", "删除"]):
            return "delete"
        if any(kw in intent_lower for kw in ["update", "更新", "修改", "modify"]):
            return "modify"
        
        return "update"  # Default


class MemoryPreflight:
    """
    Memory Preflight for Mutation
    
    Executes mandatory checks before mutation operations.
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        self.registry = CanonicalRegistry(registry_path)
        self.intent_parser = IntentParser()
        
        workspace = os.environ.get("OPENCLAW_WORKSPACE",
                                   os.path.expanduser("~/.openclaw/workspace"))
        self.evidence_dir = os.path.join(workspace, "artifacts/mutations")
        os.makedirs(self.evidence_dir, exist_ok=True)
    
    def check(self, 
              task_id: str,
              intent: str,
              target_repo: Optional[str] = None,
              action: Optional[str] = None) -> PreflightResult:
        """
        Execute preflight check.
        
        Args:
            task_id: Task identifier
            intent: Task intent/description
            target_repo: Target repository
            action: Intended action (optional, inferred from intent if not provided)
            
        Returns:
            PreflightResult with decision and details
        """
        consulted_sources = []
        
        # Gate M1: Object Resolve
        object_name = self.intent_parser.parse(intent)
        
        if not object_name:
            # Not a canonical object operation, allow
            return PreflightResult(
                decision=Decision.ALLOW,
                object_name=None,
                resolved_target=None,
                write_policy=None,
                reason="Non-canonical operation, no preflight required",
                consulted_sources=["intent_parser"],
                evidence_path=None
            )
        
        consulted_sources.append("canonical_registry")
        
        # Gate M2: Canonical Resolve
        resolved_target = self.registry.resolve_target(object_name, target_repo)
        
        if not resolved_target:
            # Cannot resolve target, block
            result = PreflightResult(
                decision=Decision.BLOCK,
                object_name=object_name,
                resolved_target=None,
                write_policy=None,
                reason=f"Cannot resolve canonical target for {object_name}",
                consulted_sources=consulted_sources,
                evidence_path=None
            )
            result.evidence_path = self._log_evidence(task_id, result)
            return result
        
        # Gate M3: Policy Check
        write_policy = self.registry.get_write_policy(object_name, target_repo)
        
        if action is None:
            action = self.intent_parser.infer_action(intent)
        
        forbidden = self.registry.get_forbidden_actions(object_name)
        
        # Check if action is forbidden
        action_violations = self._check_policy_violation(action, write_policy, forbidden)
        
        if action_violations:
            result = PreflightResult(
                decision=Decision.BLOCK,
                object_name=object_name,
                resolved_target=resolved_target,
                write_policy=write_policy,
                reason=f"Policy violation: {action_violations}",
                consulted_sources=consulted_sources,
                evidence_path=None
            )
            result.evidence_path = self._log_evidence(task_id, result)
            return result
        
        # Check if target exists for update_only
        if write_policy == "update_only":
            if action == "create":
                result = PreflightResult(
                    decision=Decision.BLOCK,
                    object_name=object_name,
                    resolved_target=resolved_target,
                    write_policy=write_policy,
                    reason="update_only policy forbids create. Target should already exist.",
                    consulted_sources=consulted_sources + ["file_system_check"],
                    evidence_path=None
                )
                result.evidence_path = self._log_evidence(task_id, result)
                return result
        
        # Gate M4: Evidence Echo
        evidence_path = self._log_evidence(task_id, PreflightResult(
            decision=Decision.ALLOW,
            object_name=object_name,
            resolved_target=resolved_target,
            write_policy=write_policy,
            reason="All gates passed",
            consulted_sources=consulted_sources,
            evidence_path=None
        ))
        
        # Gate M5: Execute or Block
        return PreflightResult(
            decision=Decision.ALLOW,
            object_name=object_name,
            resolved_target=resolved_target,
            write_policy=write_policy,
            reason="All gates passed, mutation allowed",
            consulted_sources=consulted_sources,
            evidence_path=evidence_path
        )
    
    def _check_policy_violation(self, 
                                 action: str, 
                                 write_policy: str, 
                                 forbidden: List[str]) -> List[str]:
        """Check for policy violations"""
        violations = []
        
        # Check forbidden actions
        forbidden_keywords = {
            "create": ["create", "新建", "创建"],
            "delete": ["delete", "删除"]
        }
        
        for fb in forbidden:
            fb_lower = fb.lower()
            for act, keywords in forbidden_keywords.items():
                if any(kw in fb_lower for kw in keywords):
                    if act in action:
                        violations.append(fb)
        
        # Check write policy
        if write_policy == "update_only" and action == "create":
            violations.append("update_only forbids create")
        
        if write_policy == "append_only" and action in ["create", "modify"]:
            violations.append("append_only only allows append")
        
        return violations
    
    def _log_evidence(self, task_id: str, result: PreflightResult) -> str:
        """Log evidence to file"""
        evidence = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            **result.to_dict()
        }
        
        evidence_path = os.path.join(self.evidence_dir, f"{task_id}_mutation_evidence.json")
        
        with open(evidence_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        return evidence_path
    
    def get_block_message(self, result: PreflightResult) -> str:
        """Generate human-readable block message"""
        if result.is_allowed():
            return ""
        
        return f"""🚫 MUTATION BLOCKED

Object: {result.object_name or 'N/A'}
Reason: {result.reason}
Action Attempted: modify
Canonical Target: {result.resolved_target or 'AMBIGUOUS'}
Policy: {result.write_policy or 'N/A'}

Suggestion: Use UPDATE on existing canonical target.

Evidence: {result.evidence_path or 'N/A'}
"""


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI interface for memory_preflight"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Preflight for Mutation")
    parser.add_argument("--task-id", required=True, help="Task identifier")
    parser.add_argument("--intent", required=True, help="Task intent/description")
    parser.add_argument("--repo", help="Target repository")
    parser.add_argument("--action", help="Intended action")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    preflight = MemoryPreflight()
    result = preflight.check(
        task_id=args.task_id,
        intent=args.intent,
        target_repo=args.repo,
        action=args.action
    )
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.is_allowed():
            print(f"✅ ALLOW: {result.reason}")
            if result.resolved_target:
                print(f"   Target: {result.resolved_target}")
        else:
            print(preflight.get_block_message(result))


if __name__ == "__main__":
    main()

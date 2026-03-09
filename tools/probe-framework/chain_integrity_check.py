#!/usr/bin/env python3
"""
Chain Integrity Check - Multi-step Flow Verification Mode

Verifies multi-step process integrity.
Example: Submit task → Execute → Callback → Confirm.
"""

try:
    from .probe_base import ProbeBase, ProbeResult, ProbeRegistry
except ImportError:
    from probe_base import ProbeBase, ProbeResult, ProbeRegistry

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


@ProbeRegistry.register
class ChainIntegrityCheck(ProbeBase):
    """
    Chain integrity verification mode.
    
    Verifies that multi-step processes complete correctly.
    Use when you need to validate end-to-end workflow integrity.
    """
    
    VERIFICATION_MODE = "chain_integrity_check"
    
    # Default chain steps to verify
    DEFAULT_CHAIN = [
        {"step": "input_received", "check": "existence"},
        {"step": "processing_started", "check": "existence"},
        {"step": "output_generated", "check": "existence"},
        {"step": "callback_sent", "check": "existence"}
    ]
    
    def __init__(self, name: str = "chain-integrity"):
        super().__init__(name)
    
    def check(self, dry_run: bool = False,
              chain_steps: List[Dict[str, Any]] = None,
              chain_id: str = None,
              verify_order: bool = True) -> ProbeResult:
        """
        Verify chain integrity.
        
        Args:
            dry_run: If True, return simulated success
            chain_steps: List of steps to verify
            chain_id: Specific chain to check
            verify_order: Whether to verify step order
            
        Returns:
            ProbeResult with chain verification results
        """
        import time
        start_time = time.perf_counter()
        
        if dry_run:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProbeResult.ok(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message="Dry run completed (no actual check)",
                evidence={"dry_run": True},
                duration_ms=duration_ms
            )
        
        steps = chain_steps or self.DEFAULT_CHAIN
        
        evidence = {
            "chain_id": chain_id,
            "steps_checked": [],
            "steps_passed": [],
            "steps_failed": [],
            "order_violations": []
        }
        
        all_passed = True
        last_timestamp = None
        
        # Check for chain receipts
        receipt_dir = "artifacts/receipts"
        if chain_id:
            chain_pattern = f"{chain_id}_"
        else:
            chain_pattern = ""
        
        for step in steps:
            step_name = step.get("step", "unknown")
            check_type = step.get("check", "existence")
            
            step_result = {
                "step": step_name,
                "check": check_type,
                "passed": False
            }
            
            # Check for evidence of this step
            step_evidence = self._check_step_evidence(
                step_name, 
                chain_pattern,
                receipt_dir
            )
            
            step_result["evidence"] = step_evidence
            
            if step_evidence.get("found"):
                step_result["passed"] = True
                evidence["steps_passed"].append(step_name)
                
                # Check order if required
                if verify_order and step_evidence.get("timestamp"):
                    current_ts = step_evidence["timestamp"]
                    if last_timestamp and current_ts < last_timestamp:
                        evidence["order_violations"].append({
                            "step": step_name,
                            "expected_after": last_timestamp,
                            "actual": current_ts
                        })
                    last_timestamp = current_ts
            else:
                all_passed = False
                evidence["steps_failed"].append(step_name)
            
            evidence["steps_checked"].append(step_result)
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        evidence["total_steps"] = len(steps)
        evidence["passed_count"] = len(evidence["steps_passed"])
        evidence["failed_count"] = len(evidence["steps_failed"])
        
        if all_passed:
            if evidence["order_violations"]:
                return ProbeResult.warn(
                    probe_name=self.name,
                    verification_mode=self.verification_mode,
                    message=f"Chain complete but order violations detected",
                    evidence=evidence,
                    duration_ms=duration_ms
                )
            return ProbeResult.ok(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message=f"All {len(steps)} chain steps passed",
                evidence=evidence,
                duration_ms=duration_ms
            )
        else:
            return ProbeResult.fail(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message=f"Chain incomplete: {len(evidence['steps_failed'])} steps failed",
                evidence=evidence,
                duration_ms=duration_ms
            )
    
    def _check_step_evidence(self, step_name: str, chain_pattern: str, 
                             receipt_dir: str) -> Dict[str, Any]:
        """Check for evidence of a step completion."""
        result = {"found": False}
        
        # Map step names to receipt patterns
        step_patterns = {
            "input_received": ["preflight", "contract"],
            "processing_started": ["processing", "running"],
            "output_generated": ["output", "result", "e2e"],
            "callback_sent": ["callback", "final", "completion"]
        }
        
        patterns = step_patterns.get(step_name, [step_name])
        
        if os.path.exists(receipt_dir):
            for filename in os.listdir(receipt_dir):
                if chain_pattern and chain_pattern not in filename:
                    continue
                
                for pattern in patterns:
                    if pattern in filename.lower():
                        filepath = os.path.join(receipt_dir, filename)
                        result["found"] = True
                        result["file"] = filepath
                        
                        # Try to get timestamp
                        try:
                            with open(filepath, 'r') as f:
                                data = json.load(f)
                            if "timestamp" in data:
                                result["timestamp"] = data["timestamp"]
                            elif "completed_at" in data:
                                result["timestamp"] = data["completed_at"]
                        except:
                            pass
                        
                        return result
        
        return result


# Convenience function
def run_chain_integrity_check(name: str = "chain-integrity", dry_run: bool = False, **kwargs) -> ProbeResult:
    """Run a chain integrity check."""
    probe = ChainIntegrityCheck(name)
    return probe.check(dry_run=dry_run, **kwargs)

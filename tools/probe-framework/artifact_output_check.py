#!/usr/bin/env python3
"""
Artifact Output Check - File Verification Mode

Validates artifact files exist, format correct, and content valid.
Example: Check receipt files for completeness.
"""

try:
    from .probe_base import ProbeBase, ProbeResult, ProbeRegistry
except ImportError:
    from probe_base import ProbeBase, ProbeResult, ProbeRegistry

import os
import json
from typing import List, Dict, Any, Optional


@ProbeRegistry.register
class ArtifactOutputCheck(ProbeBase):
    """
    Artifact output verification mode.
    
    Validates that output files exist and contain valid data.
    Use when you need to verify file-based outputs.
    """
    
    VERIFICATION_MODE = "artifact_output_check"
    
    def __init__(self, name: str = "artifact-output"):
        super().__init__(name)
    
    def check(self, dry_run: bool = False,
              artifact_paths: List[str] = None,
              required_fields: List[str] = None,
              check_content: bool = True) -> ProbeResult:
        """
        Check artifact files.
        
        Args:
            dry_run: If True, return simulated success
            artifact_paths: List of file paths to check
            required_fields: Fields that must be present in JSON files
            check_content: Whether to validate file content
            
        Returns:
            ProbeResult with artifact validation results
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
        
        # Default paths
        if artifact_paths is None:
            artifact_paths = [
                "artifacts/receipts",
                "artifacts/self_health"
            ]
        
        evidence = {
            "checked_paths": [],
            "missing": [],
            "invalid": [],
            "valid": []
        }
        
        all_valid = True
        total_files = 0
        
        for path in artifact_paths:
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        if f.endswith('.json'):
                            filepath = os.path.join(root, f)
                            total_files += 1
                            file_result = self._validate_file(filepath, required_fields, check_content)
                            
                            if file_result["valid"]:
                                evidence["valid"].append(filepath)
                            else:
                                all_valid = False
                                if file_result.get("missing"):
                                    evidence["missing"].append({
                                        "path": filepath,
                                        "reason": "file_not_found"
                                    })
                                else:
                                    evidence["invalid"].append({
                                        "path": filepath,
                                        "reason": file_result.get("error", "unknown")
                                    })
            
            elif os.path.isfile(path):
                total_files += 1
                file_result = self._validate_file(path, required_fields, check_content)
                if file_result["valid"]:
                    evidence["valid"].append(path)
                else:
                    all_valid = False
                    evidence["missing"].append({"path": path, "reason": "file_not_found"})
        
        evidence["checked_paths"] = artifact_paths
        evidence["total_files"] = total_files
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        if total_files == 0:
            return ProbeResult.warn(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message="No artifact files found to validate",
                evidence=evidence,
                duration_ms=duration_ms
            )
        
        if all_valid:
            return ProbeResult.ok(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message=f"All {total_files} artifact files valid",
                evidence=evidence,
                duration_ms=duration_ms
            )
        else:
            return ProbeResult.fail(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message=f"Invalid or missing artifacts: {len(evidence['invalid']) + len(evidence['missing'])} issues",
                evidence=evidence,
                duration_ms=duration_ms
            )
    
    def _validate_file(self, filepath: str, required_fields: List[str] = None, 
                       check_content: bool = True) -> Dict[str, Any]:
        """Validate a single file."""
        result = {"valid": False}
        
        if not os.path.exists(filepath):
            result["missing"] = True
            return result
        
        if filepath.endswith('.json') and check_content:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                result["valid"] = True
                
                # Check required fields
                if required_fields:
                    missing_fields = [f for f in required_fields if f not in data]
                    if missing_fields:
                        result["valid"] = False
                        result["error"] = f"Missing fields: {missing_fields}"
                
            except json.JSONDecodeError as e:
                result["error"] = f"Invalid JSON: {str(e)}"
            except Exception as e:
                result["error"] = str(e)
        else:
            result["valid"] = True
        
        return result


# Convenience function
def run_artifact_output_check(name: str = "artifact-output", dry_run: bool = False, **kwargs) -> ProbeResult:
    """Run an artifact output check."""
    probe = ArtifactOutputCheck(name)
    return probe.check(dry_run=dry_run, **kwargs)

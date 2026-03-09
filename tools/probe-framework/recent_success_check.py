#!/usr/bin/env python3
"""
Recent Success Check - Telemetry/Log Verification Mode

Checks recent success records in telemetry or logs.
Example: Check last N operations success rate.
"""

try:
    from .probe_base import ProbeBase, ProbeResult, ProbeRegistry
except ImportError:
    from probe_base import ProbeBase, ProbeResult, ProbeRegistry

import os
import json
import glob
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional


@ProbeRegistry.register
class RecentSuccessCheck(ProbeBase):
    """
    Recent success verification mode.
    
    Checks telemetry logs for recent successful operations.
    Use when you want to verify system health through historical success.
    """
    
    VERIFICATION_MODE = "recent_success_check"
    
    def __init__(self, name: str = "recent-success"):
        super().__init__(name)
        self.default_log_paths = [
            "logs/*.log",
            "logs/*.jsonl",
            "artifacts/receipts/*.json",
            "reports/**/*.json"
        ]
    
    def check(self, dry_run: bool = False, 
              log_paths: List[str] = None,
              success_threshold: float = 0.8,
              lookback_hours: int = 24,
              min_samples: int = 1) -> ProbeResult:
        """
        Check recent success rate from logs/telemetry.
        
        Args:
            dry_run: If True, return simulated success
            log_paths: Glob patterns for log files
            success_threshold: Minimum success rate (0.0-1.0)
            lookback_hours: Hours to look back
            min_samples: Minimum samples required
            
        Returns:
            ProbeResult with success rate analysis
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
        
        paths = log_paths or self.default_log_paths
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        
        total_operations = 0
        successful_operations = 0
        failed_operations = 0
        files_checked = []
        
        for pattern in paths:
            for filepath in glob.glob(pattern, recursive=True):
                if not os.path.exists(filepath):
                    continue
                
                files_checked.append(filepath)
                file_result = self._check_file(filepath, cutoff_time)
                total_operations += file_result["total"]
                successful_operations += file_result["success"]
                failed_operations += file_result["fail"]
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        if total_operations < min_samples:
            return ProbeResult.warn(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message=f"Insufficient samples: {total_operations} < {min_samples}",
                evidence={
                    "total_operations": total_operations,
                    "min_samples": min_samples,
                    "files_checked": len(files_checked)
                },
                duration_ms=duration_ms
            )
        
        success_rate = successful_operations / total_operations if total_operations > 0 else 0
        
        evidence = {
            "total_operations": total_operations,
            "successful": successful_operations,
            "failed": failed_operations,
            "success_rate": round(success_rate, 3),
            "files_checked": len(files_checked),
            "lookback_hours": lookback_hours
        }
        
        if success_rate >= success_threshold:
            return ProbeResult.ok(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message=f"Success rate {success_rate:.1%} meets threshold {success_threshold:.1%}",
                evidence=evidence,
                duration_ms=duration_ms
            )
        else:
            return ProbeResult.fail(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message=f"Success rate {success_rate:.1%} below threshold {success_threshold:.1%}",
                evidence=evidence,
                duration_ms=duration_ms
            )
    
    def _check_file(self, filepath: str, cutoff_time: datetime) -> Dict[str, int]:
        """Check a single file for success/fail indicators."""
        result = {"total": 0, "success": 0, "fail": 0}
        
        try:
            # Handle JSON files
            if filepath.endswith('.json'):
                with open(filepath, 'r') as f:
                    try:
                        data = json.load(f)
                        if isinstance(data, dict):
                            # Check for status field
                            status = data.get('status', '').lower()
                            if status in ('ok', 'success', 'completed'):
                                result["success"] += 1
                            elif status in ('fail', 'error', 'failed'):
                                result["fail"] += 1
                            result["total"] += 1
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    status = item.get('status', '').lower()
                                    if status in ('ok', 'success', 'completed'):
                                        result["success"] += 1
                                    elif status in ('fail', 'error', 'failed'):
                                        result["fail"] += 1
                                    result["total"] += 1
                    except json.JSONDecodeError:
                        pass
            
            # Handle log files
            elif filepath.endswith('.log') or filepath.endswith('.jsonl'):
                with open(filepath, 'r') as f:
                    for line in f:
                        line_lower = line.lower()
                        if 'success' in line_lower or 'ok' in line_lower:
                            result["success"] += 1
                            result["total"] += 1
                        elif 'fail' in line_lower or 'error' in line_lower:
                            result["fail"] += 1
                            result["total"] += 1
                            
        except Exception:
            pass
        
        return result


# Convenience function
def run_recent_success_check(name: str = "recent-success", dry_run: bool = False, **kwargs) -> ProbeResult:
    """Run a recent success check."""
    probe = RecentSuccessCheck(name)
    return probe.check(dry_run=dry_run, **kwargs)

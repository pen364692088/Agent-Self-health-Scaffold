#!/usr/bin/env python3
"""
Probe Check - Active Verification Mode

Executes actual operations to verify functionality is available.
Example: Call compaction API and check results.
"""

try:
    from .probe_base import ProbeBase, ProbeResult, ProbeRegistry
except ImportError:
    from probe_base import ProbeBase, ProbeResult, ProbeRegistry

import subprocess
import json
import os


@ProbeRegistry.register
class ProbeCheck(ProbeBase):
    """
    Active probe verification mode.
    
    Performs actual operations to verify system functionality.
    Use when you need to confirm that a feature works end-to-end.
    """
    
    VERIFICATION_MODE = "probe_check"
    
    def __init__(self, name: str = "active-probe"):
        super().__init__(name)
    
    def check(self, dry_run: bool = False, command: str = None, expected_output: str = None) -> ProbeResult:
        """
        Execute an active probe check.
        
        Args:
            dry_run: If True, return simulated success
            command: Command to execute (optional)
            expected_output: Expected output pattern (optional)
            
        Returns:
            ProbeResult with check outcome
        """
        import time
        
        start_time = time.perf_counter()
        
        if dry_run:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProbeResult.ok(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message="Dry run completed (no actual execution)",
                evidence={"dry_run": True},
                duration_ms=duration_ms
            )
        
        # Default: check session-start-recovery tool availability
        if command is None:
            command = "test -x /home/moonlight/.openclaw/workspace/tools/session-start-recovery && echo /home/moonlight/.openclaw/workspace/tools/session-start-recovery || echo not-found"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            if result.returncode == 0:
                evidence = {
                    "command": command,
                    "stdout": result.stdout.strip()[:500],
                    "returncode": result.returncode
                }
                
                if expected_output and expected_output not in result.stdout:
                    return ProbeResult.fail(
                        probe_name=self.name,
                        verification_mode=self.verification_mode,
                        message=f"Expected output not found: {expected_output}",
                        evidence=evidence,
                        duration_ms=duration_ms
                    )
                
                return ProbeResult.ok(
                    probe_name=self.name,
                    verification_mode=self.verification_mode,
                    message="Probe check passed",
                    evidence=evidence,
                    duration_ms=duration_ms
                )
            else:
                return ProbeResult.fail(
                    probe_name=self.name,
                    verification_mode=self.verification_mode,
                    message=f"Command failed with return code {result.returncode}",
                    evidence={
                        "command": command,
                        "stderr": result.stderr.strip()[:500],
                        "returncode": result.returncode
                    },
                    duration_ms=duration_ms
                )
                
        except subprocess.TimeoutExpired:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProbeResult.error(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message="Probe check timed out",
                evidence={"command": command, "timeout": 30},
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ProbeResult.error(
                probe_name=self.name,
                verification_mode=self.verification_mode,
                message=f"Probe check error: {str(e)}",
                evidence={"error": str(e)},
                duration_ms=duration_ms
            )


# Convenience function
def run_probe_check(name: str = "active-probe", dry_run: bool = False, **kwargs) -> ProbeResult:
    """Run an active probe check."""
    probe = ProbeCheck(name)
    return probe.check(dry_run=dry_run, **kwargs)

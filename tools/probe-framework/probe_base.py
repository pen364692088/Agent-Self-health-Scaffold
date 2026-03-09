#!/usr/bin/env python3
"""
Probe Framework - Base Classes and Result Types

Provides standardized probe result format and base class for all verification modes.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


@dataclass
class ProbeResult:
    """Standardized probe result format."""
    probe_name: str
    verification_mode: str
    status: str  # "ok", "warn", "fail", "error"
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    duration_ms: int = 0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def ok(cls, probe_name: str, verification_mode: str, message: str, 
           evidence: Optional[Dict[str, Any]] = None, duration_ms: int = 0) -> 'ProbeResult':
        """Create an 'ok' result."""
        return cls(
            probe_name=probe_name,
            verification_mode=verification_mode,
            status="ok",
            message=message,
            evidence=evidence or {},
            duration_ms=duration_ms
        )
    
    @classmethod
    def warn(cls, probe_name: str, verification_mode: str, message: str,
             evidence: Optional[Dict[str, Any]] = None, duration_ms: int = 0) -> 'ProbeResult':
        """Create a 'warn' result."""
        return cls(
            probe_name=probe_name,
            verification_mode=verification_mode,
            status="warn",
            message=message,
            evidence=evidence or {},
            duration_ms=duration_ms
        )
    
    @classmethod
    def fail(cls, probe_name: str, verification_mode: str, message: str,
             evidence: Optional[Dict[str, Any]] = None, duration_ms: int = 0) -> 'ProbeResult':
        """Create a 'fail' result."""
        return cls(
            probe_name=probe_name,
            verification_mode=verification_mode,
            status="fail",
            message=message,
            evidence=evidence or {},
            duration_ms=duration_ms
        )
    
    @classmethod
    def error(cls, probe_name: str, verification_mode: str, message: str,
              evidence: Optional[Dict[str, Any]] = None, duration_ms: int = 0) -> 'ProbeResult':
        """Create an 'error' result."""
        return cls(
            probe_name=probe_name,
            verification_mode=verification_mode,
            status="error",
            message=message,
            evidence=evidence or {},
            duration_ms=duration_ms
        )


class ProbeBase(ABC):
    """Base class for all probes."""
    
    VERIFICATION_MODE: str = "base"
    
    def __init__(self, name: str):
        self.name = name
        self.verification_mode = self.VERIFICATION_MODE
    
    @abstractmethod
    def check(self, dry_run: bool = False) -> ProbeResult:
        """
        Execute the probe check.
        
        Args:
            dry_run: If True, simulate without actual execution
            
        Returns:
            ProbeResult with status, message, and evidence
        """
        raise NotImplementedError
    
    def _measure_duration(self, func, *args, **kwargs) -> tuple:
        """Measure execution duration in milliseconds."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return result, duration_ms
    
    def save_result(self, result: ProbeResult, output_dir: str = "artifacts/self_health/probes") -> str:
        """
        Save probe result to JSON file.
        
        Args:
            result: ProbeResult to save
            output_dir: Directory to save results
            
        Returns:
            Path to saved file
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{self.name}.json")
        with open(output_path, 'w') as f:
            f.write(result.to_json())
        return output_path


class ProbeRegistry:
    """Registry for all available probes."""
    
    _probes: Dict[str, type] = {}
    
    @classmethod
    def register(cls, probe_class: type) -> type:
        """Register a probe class."""
        cls._probes[probe_class.__name__] = probe_class
        return probe_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """Get a probe class by name."""
        return cls._probes.get(name)
    
    @classmethod
    def list(cls) -> Dict[str, type]:
        """List all registered probes."""
        return cls._probes.copy()
    
    @classmethod
    def list_by_mode(cls, mode: str) -> Dict[str, type]:
        """List probes by verification mode."""
        return {
            name: probe 
            for name, probe in cls._probes.items() 
            if probe.VERIFICATION_MODE == mode
        }

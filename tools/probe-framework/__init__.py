#!/usr/bin/env python3
"""
Probe Framework

A unified verification framework for system health probes.
Provides 5 verification modes for different checking strategies.
"""

from .probe_base import ProbeBase, ProbeResult, ProbeRegistry
from .probe_check import ProbeCheck, run_probe_check
from .recent_success_check import RecentSuccessCheck, run_recent_success_check
from .artifact_output_check import ArtifactOutputCheck, run_artifact_output_check
from .synthetic_input_check import SyntheticInputCheck, run_synthetic_input_check
from .chain_integrity_check import ChainIntegrityCheck, run_chain_integrity_check

__all__ = [
    # Base classes
    'ProbeBase',
    'ProbeResult',
    'ProbeRegistry',
    
    # Probe implementations
    'ProbeCheck',
    'RecentSuccessCheck',
    'ArtifactOutputCheck',
    'SyntheticInputCheck',
    'ChainIntegrityCheck',
    
    # Convenience functions
    'run_probe_check',
    'run_recent_success_check',
    'run_artifact_output_check',
    'run_synthetic_input_check',
    'run_chain_integrity_check',
]

__version__ = '1.0.0'

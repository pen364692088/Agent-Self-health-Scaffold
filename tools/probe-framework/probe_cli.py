#!/usr/bin/env python3
"""
Probe Framework CLI

Unified command-line interface for running probes.
"""

import argparse
import sys
import os
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from probe_base import ProbeRegistry, ProbeResult
from probe_check import ProbeCheck
from recent_success_check import RecentSuccessCheck
from artifact_output_check import ArtifactOutputCheck
from synthetic_input_check import SyntheticInputCheck
from chain_integrity_check import ChainIntegrityCheck


# Mode to class mapping
MODE_CLASSES = {
    "probe_check": ProbeCheck,
    "recent_success_check": RecentSuccessCheck,
    "artifact_output_check": ArtifactOutputCheck,
    "synthetic_input_check": SyntheticInputCheck,
    "chain_integrity_check": ChainIntegrityCheck
}


def cmd_list(args):
    """List all available verification modes."""
    print("Available Verification Modes:")
    print("-" * 40)
    for mode, cls in MODE_CLASSES.items():
        doc = cls.__doc__ or ""
        first_line = doc.strip().split('\n')[0] if doc else "No description"
        print(f"  {mode}:")
        print(f"    {first_line}")
        print()
    
    print("Registered Probes:")
    print("-" * 40)
    for name, cls in ProbeRegistry.list().items():
        print(f"  {name}: {cls.VERIFICATION_MODE}")
    
    return 0


def cmd_run(args):
    """Run a specific probe or probes by mode."""
    mode = args.mode
    probe_name = args.probe_name
    dry_run = args.dry_run
    save_output = args.save
    
    if mode and mode not in MODE_CLASSES:
        print(f"Error: Unknown mode '{mode}'", file=sys.stderr)
        print(f"Available modes: {', '.join(MODE_CLASSES.keys())}", file=sys.stderr)
        return 1
    
    results = []
    
    if probe_name:
        # Run specific probe
        if mode:
            probe_cls = MODE_CLASSES[mode]
            probe = probe_cls(probe_name)
        else:
            # Try to find in registry
            probe_cls = ProbeRegistry.get(probe_name)
            if probe_cls:
                probe = probe_cls()
            else:
                print(f"Error: Unknown probe '{probe_name}'", file=sys.stderr)
                return 1
        
        result = probe.check(dry_run=dry_run)
        results.append(result)
        
    elif mode:
        # Run all probes of a mode
        probe_cls = MODE_CLASSES[mode]
        probe = probe_cls(f"{mode}-default")
        result = probe.check(dry_run=dry_run)
        results.append(result)
    
    else:
        # Run all modes
        for mode_name, probe_cls in MODE_CLASSES.items():
            probe = probe_cls(f"{mode_name}-default")
            result = probe.check(dry_run=dry_run)
            results.append(result)
    
    # Output results
    for result in results:
        print(result.to_json())
        print()
        
        if save_output:
            output_path = probe.save_result(result)
            print(f"Saved to: {output_path}")
    
    # Summary
    status_counts = {}
    for r in results:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
    
    print("Summary:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # Return non-zero if any failures
    if any(r.status in ("fail", "error") for r in results):
        return 1
    return 0


def cmd_run_all(args):
    """Run all probes in quick or full mode."""
    mode = args.mode  # quick or full
    dry_run = args.dry_run
    save_output = args.save
    
    print(f"Running all probes ({mode} mode)...")
    print("=" * 50)
    
    results = []
    
    for mode_name, probe_cls in MODE_CLASSES.items():
        probe = probe_cls(f"{mode_name}-check")
        
        # Quick mode only runs dry-run for speed
        if mode == "quick":
            result = probe.check(dry_run=True)
        else:
            result = probe.check(dry_run=dry_run)
        
        results.append(result)
        
        status_icon = {
            "ok": "✓",
            "warn": "⚠",
            "fail": "✗",
            "error": "!"
        }.get(result.status, "?")
        
        print(f"{status_icon} {mode_name}: {result.message}")
        
        if save_output:
            probe.save_result(result)
    
    print("=" * 50)
    
    # Summary
    status_counts = {}
    for r in results:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
    
    print(f"\nTotal: {len(results)} probes")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # Return non-zero if any failures
    if any(r.status in ("fail", "error") for r in results):
        return 1
    return 0


def cmd_status(args):
    """Show status of recent probe results."""
    output_dir = "artifacts/self_health/probes"
    
    if not os.path.exists(output_dir):
        print("No probe results found.")
        print(f"Expected directory: {output_dir}")
        return 0
    
    results = []
    for filename in os.listdir(output_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(output_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                results.append(data)
            except:
                pass
    
    if not results:
        print("No probe results found.")
        return 0
    
    print(f"Probe Results ({len(results)} total):")
    print("-" * 60)
    
    for r in sorted(results, key=lambda x: x.get('timestamp', '')):
        status_icon = {
            "ok": "✓",
            "warn": "⚠",
            "fail": "✗",
            "error": "!"
        }.get(r.get('status', ''), "?")
        
        name = r.get('probe_name', 'unknown')
        mode = r.get('verification_mode', 'unknown')
        msg = r.get('message', '')[:50]
        
        print(f"{status_icon} {name} [{mode}]: {msg}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Probe Framework CLI - Unified verification interface"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # list command
    parser_list = subparsers.add_parser("list", help="List available verification modes")
    parser_list.set_defaults(func=cmd_list)
    
    # run command
    parser_run = subparsers.add_parser("run", help="Run a specific probe")
    parser_run.add_argument("--mode", "-m", help="Verification mode to run")
    parser_run.add_argument("--probe-name", "-p", help="Specific probe name")
    parser_run.add_argument("--dry-run", "-n", action="store_true", 
                           help="Simulate without actual execution")
    parser_run.add_argument("--save", "-s", action="store_true",
                           help="Save results to artifacts")
    parser_run.set_defaults(func=cmd_run)
    
    # run-all command
    parser_run_all = subparsers.add_parser("run-all", help="Run all probes")
    parser_run_all.add_argument("--mode", "-m", choices=["quick", "full"], 
                                default="quick", help="Run mode (quick/full)")
    parser_run_all.add_argument("--dry-run", "-n", action="store_true",
                                help="Simulate without actual execution")
    parser_run_all.add_argument("--save", "-s", action="store_true",
                                help="Save results to artifacts")
    parser_run_all.set_defaults(func=cmd_run_all)
    
    # status command
    parser_status = subparsers.add_parser("status", help="Show recent probe results")
    parser_status.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

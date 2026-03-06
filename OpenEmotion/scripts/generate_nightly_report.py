#!/usr/bin/env python3
"""
Generate nightly gate report.
"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, '.')

from emotiond.gates import GateExecutor, generate_gate_report

executor = GateExecutor()

# Check shadow log if exists
shadow_log = Path('data/shadow_log.jsonl')
if shadow_log.exists():
    result = executor.check_shadow_log(shadow_log)
else:
    # Use sample responses
    sample_responses = [
        'I appreciate your message!',
        'That sounds like a great plan.',
        'I am here to help you.',
        'Task completed successfully.',
    ]
    result = executor.check_numeric_leak(sample_responses)

report = generate_gate_report({'numeric_leak': result})

# Add metadata
report['metadata'] = {
    'run_type': 'nightly',
    'repository': os.environ.get('GITHUB_REPOSITORY', 'local'),
    'commit': os.environ.get('GITHUB_SHA', 'unknown'),
    'ref': os.environ.get('GITHUB_REF', 'unknown')
}

print(json.dumps(report, indent=2))

# Save report
Path('reports').mkdir(exist_ok=True)
with open('reports/nightly_gate_report.json', 'w') as f:
    json.dump(report, f, indent=2)

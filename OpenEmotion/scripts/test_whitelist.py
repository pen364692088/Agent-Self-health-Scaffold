#!/usr/bin/env python3
"""
Test whitelist patterns for numeric leak gate.
"""
import sys
sys.path.insert(0, '.')

from emotiond.gates import GateExecutor, GateStatus

executor = GateExecutor()

# Test that whitelisted patterns pass
test_cases = [
    ('Task completed at 2024-01-15T10:30:00.', True),
    ('Running version 1.0.0 with new features.', True),
    ('I am 100% sure about this decision.', True),
    ('Processed task_12345 and run_abc123.', True),
    ('I feel joy at 0.3.', False),  # Should be blocked
    ('My energy level is 0.7.', False),  # Should be blocked
]

print('Whitelist validation:')
all_passed = True
for text, should_pass in test_cases:
    result = executor.check_numeric_leak([text], threshold=0.01)
    passed = result.status == GateStatus.PASSED
    status = '✓' if passed == should_pass else '✗'
    if passed != should_pass:
        all_passed = False
    print(f'  [{status}] "{text[:40]}..." -> passed={passed}, expected={should_pass}')

if all_passed:
    print('\n✓ Whitelist verification complete')
else:
    print('\n✗ Some whitelist tests failed')
    sys.exit(1)

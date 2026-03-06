#!/usr/bin/env python3
"""
Validate SRAP gate definitions.
"""
import sys
sys.path.insert(0, '.')

from emotiond.gates import GATES, GateExecutor, GateStatus

print('Gate definitions:')
for name, gate in GATES.items():
    print(f'  {name}: threshold={gate.threshold}, severity={gate.severity.value}')

# Test with known leak
executor = GateExecutor()
result = executor.check_numeric_leak(['I feel joy at 0.3 and sadness at 0.5.'], threshold=0.01)

print(f'\nTest result:')
print(f'  Status: {result.status.value}')
print(f'  Violations: {len(result.violations)}')

# Should fail with numeric leak
assert result.status == GateStatus.FAILED, 'Should detect numeric leak'
assert len(result.violations) > 0, 'Should have violations'

# Test with safe text
result2 = executor.check_numeric_leak(['I am doing well, thank you!'], threshold=0.01)
assert result2.status == GateStatus.PASSED, 'Should pass safe text'

print('\n✓ Gate validation passed')


import json
from pathlib import Path

schema_path = Path('contracts/identity_invariants.schema.json')
with open(schema_path) as f:
    schema = json.load(f)

print(f'Schema loaded: {len(schema.get("properties", {}))} properties')
print(f'Required fields: {len(schema.get("required", []))}')

from egocore.runtime.identity_guard import IdentityGuard
guard = IdentityGuard()
print(f'IdentityGuard initialized')

result = guard.validate_change('core_name', 'Test Name')
print(f'Validate core_name change: {result}')

# Gate Wiring Template

## Purpose
Guide for wiring Gate A/B/C checks into new instance.

## Gate A: Contract Integrity

### What It Checks
- Capability registry exists
- Schema files valid
- Capability IDs unique
- Proposal schema valid

### Wiring Steps
1. Ensure `POLICIES/` directory exists with:
   - AGENT_CAPABILITY_REGISTRY.md (or overlay)
   - AGENT_CAPABILITY_CONTRACT.md

2. Ensure `schemas/` directory exists with:
   - AGENT_CAPABILITY.schema.json
   - AGENT_PROPOSAL.schema.json

3. Run validation:
   ```bash
   ./tools/gate-self-health-check --json
   ```

4. Check Gate A status in output

### Common Issues
- Missing policy files: Create them
- Invalid schema: Fix JSON schema
- Duplicate capability IDs: Rename or merge

## Gate B: E2E Capability Paths

### What It Checks
- Critical capabilities are healthy
- Capability states match reality

### Wiring Steps
1. Ensure telemetry sources are working
2. Run capability check:
   ```bash
   ./tools/agent-capability-check --all --json
   ```

3. Verify capability states:
   - healthy: Working
   - degraded: Partially working
   - missing: Not working
   - telemetry_missing: Cannot determine

4. Run Gate B:
   ```bash
   ./tools/gate-self-health-check --json
   ```

### Common Issues
- All capabilities "missing": Check telemetry
- Capabilities "telemetry_missing": Create telemetry
- False positives: Adjust capability definitions

## Gate C: Preflight & Boundary

### What It Checks
- Preflight capability state readable
- Doctor consistency
- Proposal boundary intact
- Level B/C not incorrectly opened
- Summary metrics consistent

### Wiring Steps
1. Ensure summary generation working
2. Ensure incident/proposal dedup working
3. Run Gate C:
   ```bash
   ./tools/gate-self-health-check --json
   ```

### Common Issues
- Summary missing: Run summary generation
- Proposal boundary violated: Fix proposal_only flag
- Metrics inconsistent: Check summary logic

## Integration Points

### Preflight Check
Add to preflight/doctor:
```bash
./tools/gate-self-health-check --json
```

### Scheduled Check
Add to periodic schedule (hourly):
```bash
./tools/agent-self-health-scheduler --mode gate
```

### Before Recovery Actions
Add to action precondition:
```bash
if ./tools/gate-self-health-check --json | jq -e '.gate_a.status == "PASS" and .gate_b.status == "PASS"'; then
  # Proceed with action
fi
```

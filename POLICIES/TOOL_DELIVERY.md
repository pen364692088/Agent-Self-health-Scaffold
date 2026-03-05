# Tool Delivery Gates Protocol v1.0

**Purpose**: Ensure all tool deliveries meet quality gates before deployment.
**Effective Date**: 2026-03-04
**Applies To**: All tool implementations, wrappers, integrations, and handlers.

---

## Overview

Every tool delivery MUST pass three gates before being marked complete:

```
Gate A: Contract Validation (args/result schema + drift detection)
Gate B: E2E Testing (real wrapper/transport with happy + bad args)
Gate C: Preflight Check (tool_doctor run with doctor_report.json)
```

**Final Deliverable MUST Include Evidence Blocks**:
```markdown
## EVIDENCE_GATE_A
- Schema validated: [file paths]
- Drift detection: [PASS/FAIL + details]
- Error format: [standardized]

## EVIDENCE_GATE_B
- E2E happy path: [test output or screenshot]
- E2E bad args: [error handling verified]

## EVIDENCE_GATE_C
- tool_doctor output: [doctor_report.json summary]
- Health checks: [list of passed checks]
```

---

## Gate A: Contract Validation

### Requirements
1. **Input Schema**: All function args must have a defined schema (JSON Schema or equivalent)
2. **Output Schema**: All return values must have a defined schema
3. **Drift Detection**: Runtime args/return must match schema (no undocumented fields)
4. **Error Format**: Errors must follow standardized format:
   ```json
   {
     "error": {
       "type": "error_type",
       "message": "Human-readable message",
       "code": "ERROR_CODE",
       "details": {}
     }
   }
   ```

### Validation Tools
```bash
# Validate schema
tools/contract-validator <tool_path> --schema-dir schemas/

# Drift detection
tools/drift-detector <tool_path> --baseline baselines/
```

### Pass Criteria
- All args validated against schema
- No undocumented fields in runtime
- Errors follow standard format
- Documentation matches implementation

---

## Gate B: E2E Testing

### Requirements
1. **Happy Path**: Tool executes successfully with valid inputs
2. **Bad Args**: Tool gracefully handles invalid inputs
3. **Real Transport**: Must use actual wrapper/transport (no mocks for external services)
4. **Idempotency**: Repeated calls with same input produce same result (where applicable)

### Test Structure
```bash
# Run E2E tests
tools/e2e-runner <tool_path> --cases tests/e2e/

# Test cases required:
# - tests/e2e/<tool>_happy.yaml   - success case
# - tests/e2e/<tool>_badargs.yaml - error handling case
```

### Test Case Format (YAML)
```yaml
name: tool_name_happy
tool: tools/tool_name
input:
  arg1: value1
  arg2: value2
expect:
  status: success
  output_contains:
    - "expected_field"
  schema_valid: true
```

```yaml
name: tool_name_badargs
tool: tools/tool_name
input:
  arg1: invalid_value
expect:
  status: error
  error_code: INVALID_ARG
  error_contains: "arg1 must be"
```

### Pass Criteria
- Happy path test passes
- Bad args test passes
- No uncaught exceptions
- Proper error messages returned

---

## Gate C: Preflight Check (tool_doctor)

### Requirements
1. **Configuration Check**: All required config present
2. **Port/Endpoint Check**: External services reachable
3. **Health Check**: Tool responds to health queries
4. **Sample Call**: Basic invocation works

### Running tool_doctor
```bash
# Standard run
tools/tool_doctor <tool_path>

# CI mode (non-interactive, exit codes)
tools/tool_doctor <tool_path> --ci

# Output: doctor_report.json
```

### doctor_report.json Schema
```json
{
  "tool": "tools/tool_name",
  "timestamp": "2026-03-04T02:00:00Z",
  "status": "healthy|degraded|unhealthy",
  "checks": [
    {
      "name": "config",
      "status": "pass|fail|warn",
      "message": "All required config present",
      "details": {}
    },
    {
      "name": "connectivity",
      "status": "pass|fail|warn",
      "message": "Endpoint reachable",
      "latency_ms": 42
    },
    {
      "name": "health",
      "status": "pass|fail|warn",
      "message": "Health check passed"
    },
    {
      "name": "sample_call",
      "status": "pass|fail|warn",
      "message": "Sample invocation successful",
      "response_time_ms": 150
    }
  ],
  "summary": {
    "passed": 4,
    "failed": 0,
    "warnings": 0
  }
}
```

### Pass Criteria
- All checks pass OR have acceptable warnings
- No failed checks
- doctor_report.json generated

---

## Bypass Mechanism

In emergency situations, gates can be bypassed:

```bash
# Disable all gates
export GATES_DISABLE=1

# Or via CLI flag
tools/tool_doctor <tool_path> --no-gates

# Or in config
echo "GATES_DISABLE=1" >> .env
```

**Bypass must be documented**:
- Why gates were bypassed
- What risks were accepted
- When gates will be re-enabled

---

## Enforcement

### Local Development
- Pre-commit hooks run Gate A (schema validation)
- Pre-push hooks run Gates A + B
- tool_doctor available on-demand

### CI/CD Pipeline
- Gate A runs on every PR
- Gate B runs on every PR
- Gate C runs on every PR
- All gates must pass for merge

### File Paths That Trigger Gates
```
tools/**
integrations/**
handlers/**
schemas/**
```

---

## Checklist for Tool Delivery

Before marking any tool task as complete, verify:

- [ ] Input schema defined and validated
- [ ] Output schema defined and validated
- [ ] Error format standardized
- [ ] Happy path E2E test passes
- [ ] Bad args E2E test passes
- [ ] tool_doctor runs successfully
- [ ] doctor_report.json generated with all checks passing
- [ ] Evidence blocks included in deliverable

---

## References

- Schema validation: `tools/contract-validator`
- Drift detection: `tools/drift-detector`
- E2E testing: `tools/e2e-runner`
- Preflight checks: `tools/tool_doctor`
- CI workflow: `.github/workflows/tool-gates.yml`

---

*Document created: 2026-03-04*
*Last updated: 2026-03-04*
*Owner: OpenClaw Tooling Team*

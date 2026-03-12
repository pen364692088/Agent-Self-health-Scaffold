# Recovery Policy

The recovery policy defines how the system should respond to failures detected by the Gate Runner or the E2E test suite.

## General Principles
- **Fast Fail** – Detect issues early and abort the pipeline.
- **Self‑Healing** – Attempt automated remediation where feasible.
- **Escalation** – If automated steps fail, notify on‑call engineers with diagnostic artifacts.

## Failure Scenarios & Automated Actions

| Failure Type | Automated Recovery Action | Manual Follow‑up |
|-------------|---------------------------|-----------------|
| Gate A (lint) error | Re‑run linter with `--fix` flag. | Review lint violations if still present. |
| Gate B (coverage) drop | Trigger test suite with `--collect‑coverage`. | Investigate missing tests. |
| Gate C (vulnerability) found | Run `pip‑freeze` → update vulnerable packages. | Perform security audit if high severity CVEs remain. |
| E2E test failure | Re‑run failing test case with verbose logging. | Debug the specific scenario; consult logs. |

## Rollback Strategy
If a deployment passes all gates but a downstream health check fails, the system should:
1. Stop traffic to the new version.
2. Re‑deploy the previous stable release.
3. Record the rollback event in the audit log.

## Documentation
All recovery actions should be logged to `logs/recovery.log` for post‑mortem analysis.

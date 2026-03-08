# ALWAYS_ON_BASELINE

## Current Baseline
- `INSTANCE_1_PROVEN`
- `MAIN_SYSTEM_ALWAYS_ON_PENDING`

## Wiring Implemented So Far
- quick mode scheduler tool added: `tools/agent-self-health-scheduler`
- gate checker added: `tools/gate-self-health-check`
- runtime telemetry files now produced under `artifacts/self_health/runtime/`
- systemd timers added for full mode and gate mode
- heartbeat policy updated to invoke quick mode silently

## Not Yet Proven
- quick mode has not yet been soak-validated across repeated heartbeat cycles
- Gate integration is baseline-level, not yet rich component coverage
- callback/mailbox telemetry is present, but mailbox path still uses file-based heuristic evidence
- final always-on verdict not issued

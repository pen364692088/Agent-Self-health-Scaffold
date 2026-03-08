# ALWAYS_ON_ROLLBACK_PLAN

## Trigger Conditions
- quick/full/gate run storm detected
- heartbeat delay impact unacceptable
- runtime telemetry stops refreshing
- gate output becomes inconsistent or unexplained
- summary / incident / proposal artifact growth abnormal

## Rollback Steps
1. `systemctl --user stop agent-self-health-full.timer agent-self-health-gate.timer`
2. remove or comment the quick mode heartbeat hook if it is causing main-loop pressure
3. keep `tools/gate-self-health-check --json` available as read-only manual gate
4. preserve runtime artifacts for audit
5. revert project state label to `MANUAL_RUN_PROVEN_BUT_ALWAYS_ON_NOT_READY`

## Minimum Safe Mode
- manual quick: `tools/agent-self-health-scheduler --mode quick --force --json`
- manual full: `tools/agent-self-health-scheduler --mode full --force --json`
- manual gate: `python3 tools/gate-self-health-check --json`
- Level B/C remain proposal-only

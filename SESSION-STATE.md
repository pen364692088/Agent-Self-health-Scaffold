# Session State

**Purpose**: 恢复主骨架 - 稳定且关键的信息

**Baseline**: v1.1.1 STABLE (FROZEN)
**Updated**: 2026-03-08T14:15:45-05:00

---

## Current Objective
按顺序实施 OpenClaw self-health always-on integration：先固化 always-on policy，再完成 quick/full/gate 默认链路接线、runtime telemetry 持续落盘、安全控制与回退、自动流转、Gate 常驻化，最后做 soak 与 final verdict。

## Current Phase
🚧 OAI-5/OAI-3/OAI-4 baseline landed: scheduler safety controls are observable, auto-flow skeleton is connected, Gate history is continuously written. Next phase is richer telemetry truth + short soak.

## Current Branch / Workspace
- Branch: openviking-l2-bugfix
- Workspace: ~/.openclaw/workspace

---

## Delivered (Scaffold v1)
- 'POLICIES/AGENT_SELF_HEALTH_POLICY.md'
- 'POLICIES/AGENT_HEALTH_STATE.schema.json'
- 'POLICIES/AGENT_INCIDENT.schema.json'
- 'tools/agent-health-check'
- 'tools/agent-health-summary'
- 'tools/agent-incident-report'
- 'tools/agent-self-heal'
- 'artifacts/self_health/{state,incidents,proposals,recovery_logs,audit}/'
- 'tests/test_agent_self_health.py'

## Delivered (Always-On Wiring v0/v1)
- 'POLICIES/OPENCLAW_ALWAYS_ON_POLICY.md'
- 'tools/agent-self-health-scheduler'
- 'tools/gate-self-health-check'
- 'artifacts/self_health/runtime/{heartbeat_status,callback_worker_status,mailbox_worker_status,summary_status}.json'
- 'artifacts/self_health/runtime/{run_history,dedup_ledger}.jsonl/json'
- 'artifacts/self_health/always_on/{ALWAYS_ON_BASELINE,ALWAYS_ON_ROLLBACK_PLAN,ALWAYS_ON_PROGRESS}.md'
- 'artifacts/self_health/always_on/{always_on_metrics,gate_report_latest}.json'
- 'templates/systemd/agent-self-health-{full,gate}.{service,timer}'
- heartbeat quick-mode hook appended to 'HEARTBEAT.md'
- user systemd timers enabled: 'agent-self-health-full.timer', 'agent-self-health-gate.timer'

## Validation Status
- 'pytest -q tests/test_agent_self_health.py'
- 'pytest -q tests/test_main_system_always_on_wiring.py'
- manual smoke:
  - 'tools/agent-self-health-scheduler --mode quick --force --json'
  - 'tools/agent-self-health-scheduler --mode full --force --json'
  - 'tools/agent-self-health-scheduler --mode gate --force --json'
  - 'python3 tools/gate-self-health-check --json'
  - 'systemctl --user status agent-self-health-full.timer'
  - 'systemctl --user status agent-self-health-gate.timer'

## Next Actions
1. Improve callback-worker/mailbox telemetry truth to reduce heuristic gaps
2. Expand Gate A/B/C explanations and component-level semantics
3. Run short always-on soak and collect evidence for intermediate status
4. Only then judge whether state can move to 'WIRING_ACTIVE_BUT_SOAK_PENDING'

## Blockers / Limits
- callback-worker telemetry currently exposes a real degraded signal while service is inactive
- mailbox-worker telemetry is still file/flow heuristic rather than process-backed
- proposal auto-flow path is wired but not yet validated under a sustained degraded scenario
- final verdict must remain evidence-based; always-on is not yet declared active

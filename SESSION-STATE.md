# Session State

**Purpose**: 恢复主骨架 - 稳定且关键的信息

**Baseline**: v1.1.1 STABLE (FROZEN)
**Updated**: 2026-03-08T14:12:52-05:00

---

## Current Objective
按顺序实施 OpenClaw self-health always-on integration：先固化 always-on policy，再完成 quick/full/gate 默认链路接线、runtime telemetry 持续落盘、安全控制与回退、自动流转、Gate 常驻化，最后做 soak 与 final verdict。

## Current Phase
🚧 OAI-0/OAI-1/OAI-2 initial wiring landed: policy + scheduler + gate checker + runtime telemetry + systemd timers; next focus is OAI-5 safety hardening and OAI-3/OAI-4 automatic flow enrichment.

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

## Delivered (Always-On Wiring v0)
- 'POLICIES/OPENCLAW_ALWAYS_ON_POLICY.md'
- 'tools/agent-self-health-scheduler'
- 'tools/gate-self-health-check'
- 'artifacts/self_health/runtime/{heartbeat_status,callback_worker_status,mailbox_worker_status,summary_status}.json'
- 'artifacts/self_health/runtime/run_history.jsonl'
- 'artifacts/self_health/always_on/{ALWAYS_ON_BASELINE,ALWAYS_ON_ROLLBACK_PLAN}.md'
- 'templates/systemd/agent-self-health-{full,gate}.{service,timer}'
- heartbeat quick-mode hook appended to 'HEARTBEAT.md'
- user systemd timers enabled: 'agent-self-health-full.timer', 'agent-self-health-gate.timer'

## Validation Status
- 'pytest -q tests/test_agent_self_health.py'
- 'pytest -q tests/test_main_system_always_on_wiring.py'
- manual smoke:
  - 'tools/agent-self-health-scheduler --mode quick --force --json'
  - 'tools/agent-self-health-scheduler --mode full --force --json'
  - 'python3 tools/gate-self-health-check --json'
  - 'systemctl --user status agent-self-health-full.timer'
  - 'systemctl --user status agent-self-health-gate.timer'

## Next Actions
1. Harden OAI-5: richer lock/cooldown/dedup/budget observability and rollback proofs
2. Enrich OAI-3: capability / incident / proposal / summary auto flow beyond baseline scheduler writes
3. Enrich OAI-4: Gate A/B/C explanations and main-chain consumption semantics
4. Run short soak and produce always-on verdict artifacts only after evidence is sufficient

## Blockers / Limits
- quick mode heartbeat integration is policy-hook based and still needs repeated soak evidence
- callback-worker telemetry currently reports degraded when service is inactive; this is evidence, not a bug mask
- mailbox-worker telemetry is currently file/flow heuristic, not process-backed service telemetry
- final verdict must remain evidence-based; always-on is not yet declared active

# Working Buffer

**Updated**: 2026-03-08T14:03:04-05:00

---

## Active Focus
按 execution checklist 顺序把 self-health 从 manual-run proven 接入为 OpenClaw 主系统 default always-on。

## Immediate order
1. OAI-0: 固化 always-on policy / 状态机 / rollback
2. OAI-1: quick/full/gate 默认链路接线
3. OAI-2: runtime telemetry 持续落盘
4. OAI-5: lock / cooldown / dedup / budget / rollback
5. OAI-3/OAI-4: 自动流转 + Gate 常驻
6. OAI-6: soak + final verdict

## Constraints
- 不把手动运行说成 always-on
- 不把后台脚本说成默认链路
- Level B/C 保持 proposal-only
- 不破坏 INSTANCE_1_PROVEN 基线

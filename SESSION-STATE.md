## Current Objective
OpenClaw 无人监管续跑闭环补齐（修复 restart 后恢复链路的裸命令调用）

## Phase
VERIFY

## Branch
main

## Blocker
需要你再重启一次，验证 gateway 日志里不再出现 `session-start-recovery: command not found`，并确认是否出现 recovery/apply 正向证据。

---

## 最新推进
- 已确认 `tools/session-route` 本身使用绝对路径调用 `tools/session-start-recovery`
- 已确认故障更可能来自 workspace 内运行指令/检查脚本仍使用裸命令 `session-start-recovery`
- 已统一修复以下调用点为绝对路径：
  - `AGENTS.md`
  - `HEARTBEAT.md`
  - `scripts/run_session_continuity_checks.py`
  - `tools/probe-framework/probe_check.py`
- 已通过最小本地验证：
  - Python compile 通过
  - `~/.openclaw/workspace/tools/session-start-recovery --recover --json` 可正常执行

## 当前结论
- 当前最直接的 PATH 级断点已被修掉
- 但是否真正修复了“restart 后 runtime 自动恢复链路”还需要一次重启后的真实验证
- 如果重启后日志里仍出现同类报错，说明实际调用源不在当前 workspace 这些文件里，而在 service/hook 上游环境

## Next
- 提交本次绝对路径修复
- 让用户再重启一次
- 复查 gateway 日志与 continuation/recovery/apply 痕迹

## Updated
2026-03-11 13:37 CDT

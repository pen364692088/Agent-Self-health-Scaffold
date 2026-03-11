## Current Objective
OpenClaw 重启后自动续跑能力已接入主循环与启动恢复路径。

## Phase
CLOSEOUT

## Branch
main

## Blocker
None

---

## 最新推进
- 已实现 durable auto-resume MVP：`tools/auto-resume-orchestrator`
- 已接入 gateway 启动路径：`auto-resume-orchestrator.service`
- 已进一步接入主循环：`tools/agent-self-health-scheduler`
  - quick/full/gate 模式都会顺手触发一次低风险 auto-resume 检查
  - 实际幂等、防重入、cooldown、lease 仍由 `auto-resume-orchestrator` 自己负责
- 新增主循环接线测试：
  - `tests/test_auto_resume_main_loop_wiring.py`
- 本轮验证测试通过：
  - `tests/test_auto_resume_main_loop_wiring.py`
  - `tests/test_auto_resume_orchestrator.py`
  - `tests/test_main_system_always_on_wiring.py`
- 当前新增提交：
  - `16761d9` feat: wire auto-resume into main scheduler loop
  - `e4fcbda` docs: add closeout evidence reports

## 当前结论
- auto-resume 现在不是只靠“启动时扫一次”，而是已经进入 always-on 主循环。
- 主链为：
  1. gateway 启动时 one-shot 恢复
  2. main scheduler loop 持续低频补扫
- 这样即使启动窗口错过一次，后续主循环仍可幂等接管。

## Next
- closeout docs 已最小化提交；下一步若继续收口，优先决定是否单独整理剩余未跟踪草稿，或直接保持为本地工作痕迹不入库。
- 如需继续增强功能，可补：
  - orphan reclaim 语义
  - recovery markers
  - 更细失败分类与告警

## Updated
2026-03-11 14:31 CDT

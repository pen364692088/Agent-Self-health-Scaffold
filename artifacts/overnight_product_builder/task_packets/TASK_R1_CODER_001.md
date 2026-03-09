# Task Packet: Coder Round 1

## Task ID
TASK_R1_CODER_001

## Round ID
ROUND_1

## Role
coder

## Objective
为 ReleasePilot 项目产出第一轮可执行资产，包括：
1. Landing page 文案
2. README.md
3. FAQ.md
4. Demo 脚本
5. MVP 目录骨架
6. 初版 specs

## Context Summary
ReleasePilot 是一个 AI 驱动的发版文档生成工具，从 git commits 自动生成：
- Changelog
- Release Notes
- Deployment Checklist
- Risk Assessment
- Rollback Guide
- Handoff Summary

目标用户：工程团队（10-100人）和独立开发者。

## Allowed Scope
- 创建目录：/home/moonlight/Project/Github/MyProject/IdearFactory/IdearFactory/workspace/incubation/releasepilot_mvp/
- 产出文档：README.md, FAQ.md, docs/, specs/
- 产出 landing page 文案：landing/
- 产出 demo 脚本：scripts/
- 产出测试样例：tests/

## Forbidden Scope
❌ 不得动现有核心项目主链路
❌ 不得假装已经有真实用户反馈
❌ 不得伪造成交数据
❌ 不得发布到生产环境
❌ 不得接入真实支付

## Required Outputs
1. `releasepilot_mvp/README.md` - 项目说明
2. `releasepilot_mvp/FAQ.md` - 常见问题
3. `releasepilot_mvp/landing/index.md` - Landing page 文案
4. `releasepilot_mvp/docs/SPEC.md` - 产品规格
5. `releasepilot_mvp/scripts/demo.sh` - Demo 脚本
6. `releasepilot_mvp/docs/ARCHITECTURE.md` - 架构说明

## Acceptance Criteria
- [ ] 所有文件已创建
- [ ] README 包含：安装、使用、示例
- [ ] FAQ 包含至少 10 个常见问题
- [ ] Landing page 有明确的 value proposition
- [ ] Demo 脚本可执行（dry-run 模式）
- [ ] 架构文档清晰

## Stop Conditions
- 完成所有 Required Outputs
- 或遇到技术阻塞（需报告原因）

## Notes / Assumptions
- 这是 proposal 阶段，不是最终商业决策
- 假设用户是 GitHub 用户
- 假设用户熟悉 CLI 工具
- 保持文档简洁、实用

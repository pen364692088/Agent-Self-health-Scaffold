# Working Buffer

**Updated**: 2026-03-08T10:31:00-06:00

---

## Active Focus
做一个受治理的 Agent self-health layer，不做无限自改写系统。

## Working assumptions
- 优先复用现有 doctor / callback / heartbeat / project-check / gate 工具
- 先把“会看见问题、会说清问题”做稳，再开放 Level A 自愈
- Level B/C 先只提案，不执行
- 所有自动动作都要落 incident + recovery log + verification result

## First implementation cut
- policy document
- health state schema
- incident schema
- health checker
- health summary
- incident generator
- whitelist-only self-heal executor
- proposal generator scaffold

# Working Buffer

## Focus
收最后一段：hard-block-only 明确化 + 恢复验证报告 + 提交。

## What Changed
- 新 truth layer 已经落地，不再只靠 WORKFLOW_STATE.json
- session-start-recovery 启动时会同步 RUN_STATE
- callback / advance 链路在关键节点已写 durable checkpoints

## Risk
- 历史 TASK_LEDGER 中残留的旧 pending 测试任务会污染 recover 判断
- 现在 hard_block 类型集合已经存在，但还分散在脚本里，下一步应抽成单一判定源

## Minimal Finish Line
- 恢复动作只分：auto-continue / hard-block
- 普通失败先 repairing / retrying，不直接 ask user
- 验证 restart / phase complete / 普通失败三条链路

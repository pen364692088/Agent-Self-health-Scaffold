# Working Buffer

## Focus
把 restart 后 recovery 的 PATH 断点先消掉，再做一次真机复测。

## What Changed
- 已排除 `tools/session-route` 本体为问题源（本体已用绝对路径）
- 已修复 workspace 内可见的裸 `session-start-recovery` 调用
- 最小自测通过：恢复工具可执行，Python 文件可编译

## Remaining Uncertainty
- 还不能证明 restart hook 已真正进入 apply/continuation
- 需要一次新的 restart 后日志证据

## Minimal Finish Line
- commit 当前修复
- 用户重启
- 复查日志是否消失 `command not found`

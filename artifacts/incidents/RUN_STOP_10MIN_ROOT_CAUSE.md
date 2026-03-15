# Phase 4: 根因分类

## 现象
OpenClaw 在执行任务约 10 分钟后自动停止/中断

## 根因
**OpenClaw CLI cron 命令的默认 timeout 被设置为 600000ms (10分钟)**

## 证据

### 代码位置
- 文件: `src/cli/cron-cli/register.cron-simple.ts`
- 行号: 95
- 代码:
```typescript
if (command.getOptionValueSource("timeout") === "default") {
  opts.timeout = "600000";  // 600000ms = 600s = 10分钟
}
```

### 调用链路
1. 用户执行 `openclaw cron run <id>`
2. 命令进入 `registerCronSimpleCommands` 函数
3. 如果用户未指定 `--timeout` 参数，则使用默认值
4. 默认 timeout 被强制设置为 "600000" (600000ms = 10分钟)
5. 该 timeout 传递给 `callGatewayFromCli`
6. Gateway 在 10 分钟后强制终止任务

### 根因分类
根据任务单要求，归为以下类别：

**类别 2: OpenClaw 任务运行器 step/task timeout**

具体说明:
- 这不是外层 supervisor/systemd 超时
- 不是会话 lease/owner 过期
- 不是 tool_doctor 或 Gate C 子进程挂起
- 不是 stdout/stderr 管道阻塞
- 不是 sandbox/worktree 生命周期问题
- 不是未捕获异常

而是 **CLI 层面的默认 timeout 配置错误**

## 影响范围
- 所有使用 `openclaw cron run` 命令且未显式指定 `--timeout` 的任务
- 长耗时任务（>10分钟）会被强制终止

## 修复方案
将默认 timeout 从 600000ms (10分钟) 改为更合理的值，如:
- 3600000ms (60分钟) - 与 job-spec.schema.json 默认值一致
- 或移除强制默认值，使用 Gateway 层面的默认配置

# CC-Godmode 任务模板: 项目检查

## 任务类型
`project-check`

## 描述
标准化项目检查流程，避免长对话卡死。

## 核心原则
1. **主会话只做 orchestration** - 不读原始长日志
2. **一个 session 只做一个 phase** - 做完就退出
3. **worker 只交付 artifact** - status.json + summary.md + raw.log
4. **进度查询只读状态文件** - 不打到执行 worker

## 标准流程

### 初始化
```bash
project-check init /path/to/repo
# 输出: check_YYYYMMDD_HHMMSS_xxxxxxxx
```

### 执行 Phase
```bash
# 方式1: 手动逐个执行
project-check spawn <check_id>
project-check-advance <check_id>

# 方式2: 自动推进（推荐）
project-check-advance <check_id> --auto-spawn
```

### 查询进度
```bash
project-check status <check_id>
```

### 获取报告
```bash
cat artifacts/project_check/<check_id>/final/one_liner.txt
```

## 5 个标准 Phase

| Phase | 名称 | 超时 | 依赖 |
|-------|------|------|------|
| A | Repo Snapshot | 60s | 无 |
| B | Fast Tests | 300s | 无 |
| C | Testbot E2E | 600s | B |
| D | Hard Gate | 300s | C |
| E | Aggregation | 60s | D |

## 6 条硬规则

1. 同一 session 禁止跨 phase
2. phase 完成后必须退出 session
3. 进度查询只读取 status.json
4. raw log 只落盘，不回灌聊天
5. 失败后只做定点复盘
6. 总检查必须先有 manifest

## 工具位置

- `tools/project-check` - 主入口
- `tools/project-check-phase` - Phase worker
- `tools/project-check-advance` - 自动推进

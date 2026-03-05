# 诊断记录: subtask-orchestrate SIGTERM

**时间**: 2026-03-03 15:52 CST
**问题**: `subtask-orchestrate run` 被 SIGTERM 中止

## 根因分析

1. **Task 参数包含换行符**
   - 原始任务描述有 4 行内容
   - Shell 命令行解析时换行符导致截断

2. **中文字符**
   - 中文冒号、括号可能在某些 shell 环境下导致问题

3. **SIGTERM 来源**
   - 非 Python 脚本内部错误（无 traceback）
   - 来自外部进程管理器或 shell 解析器

## 修复方案

### 方案 A: JSON 模式 (推荐)
```bash
~/.openclaw/workspace/tools/subtask-orchestrate run --json "单行任务描述" -m <model>
```

### 方案 B: 任务描述写入文件
```bash
echo "详细任务描述..." > /tmp/task.txt
~/.openclaw/workspace/tools/subtask-orchestrate run "$(cat /tmp/task.txt)" -m <model>
```

### 方案 C: 简化描述
只传递简短摘要，详细内容通过 SESSION-STATE.md 或任务文件传递

## 约定更新

1. 长任务描述 → 使用 SESSION-STATE.md + 简短 task 参数
2. 复杂字符 → 避免 shell 直接传递，使用文件或 JSON 模式
3. 任务细节 → 子代理读取 SESSION-STATE.md 获取上下文

## 修改文件

- TOOLS.md 添加此约定
- 更新 SESSION-STATE.md 结构

---
Added: 2026-03-03 16:06 CST

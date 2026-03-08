# Session Continuity Test Plan v1.1

## Overview

本文档定义了 Session Continuity v1.1 的完整测试计划。

## Test Categories

### 1. Recovery Tests (Task 1)

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| R1 | 新 session 第一条实质性回复前恢复完成 | 恢复在回复前执行 |
| R2 | 无状态文件时正常处理 | 不报错，继续正常流程 |
| R3 | 有冲突时正确裁决 | 按优先级规则裁决 |
| R4 | 恢复失败时设置 uncertainty_flag | flag = true |
| R5 | 恢复摘要正确生成 | 生成 JSON + MD 文件 |

### 2. Conflict Resolution Tests (Task 2)

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| C1 | SESSION-STATE 与 repo 分支冲突 | Repo 分支优先 |
| C2 | handoff 与 SESSION-STATE 目标冲突 | 较新文件优先 |
| C3 | 状态文件过期 (>72h) | 标记 stale 警告 |
| C4 | 关键字段缺失 | 从其他来源恢复或提示 |
| C5 | WAL 与状态文件不一致 | WAL 优先 |

### 3. WAL Tests (Task 3)

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| W1 | 原子写入成功 | 文件创建，hash 正确 |
| W2 | 中断后可从 WAL 恢复 | 最新有效 entry 可回放 |
| W3 | WAL append 顺序正确 | 时间戳递增 |
| W4 | WAL entry 格式正确 | 包含所有必需字段 |

### 4. Concurrency Tests (Task 4)

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| L1 | 获取锁成功 | lock 文件创建 |
| L2 | 释放锁成功 | lock 文件删除 |
| L3 | 检测 stale lock | 自动清理 |
| L4 | 并发写入不覆盖 | 后写入等待或报错 |

### 5. Integration Tests (Task 5)

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| I1 | 完整恢复流程 | preflight → recover → summary |
| I2 | context > 80% 时 handoff | 先 handoff 再压缩 |
| I3 | Gate A/B/C 全通过 | 所有 gate 返回 success |

## Gate Definitions

### Gate A: Protocol / Document / Schema Existence

检查所有必需文件是否存在：
- docs/session_continuity/*.md
- tools/session-start-recovery
- tools/state-write-atomic
- tools/state-journal-append
- tools/state-lock

### Gate B: E2E Recovery Flow

执行完整的恢复流程：
- preflight 检查
- recover 执行
- summary 生成

### Gate C: Tool Chain Availability

检查所有工具可执行：
- 所有工具存在且可执行
- 健康检查返回正常

## Test Execution

### Manual Tests

```bash
# Run all tests
pytest tests/session_continuity/test_session_continuity_v11.py -v

# Run specific test class
pytest tests/session_continuity/test_session_continuity_v11.py::TestSessionRecovery -v

# Run with coverage
pytest tests/session_continuity/test_session_continuity_v11.py --cov=tools
```

### Gate Checks

```bash
# Run all gates
python scripts/run_session_continuity_checks.py --gate all --report

# Run specific gate
python scripts/run_session_continuity_checks.py --gate A

# Run gates + pytest
python scripts/run_session_continuity_checks.py --gate all --test --report
```

### Continuous Integration

Gate 检查应集成到 CI 流程中：
- 每次提交运行 Gate A
- 每次合并运行 Gate A + B
- 发布前运行全部 Gate

## Test Data

### Fixtures

测试数据存放在 `tests/session_continuity/fixtures/`:
- sample_session_state.md
- sample_working_buffer.md
- sample_handoff.md
- sample_wal.jsonl

### Mock Data

对于需要 mock 的测试：
- 使用临时目录
- 测试后清理

## Reporting

测试报告生成到：
```
artifacts/session_continuity/v1_1/VALIDATION_REPORT.md
artifacts/session_continuity/v1_1/VALIDATION_REPORT.json
```

## Acceptance Criteria

v1.1 只有在以下条件全部满足时才算通过：

1. ✅ 所有 Gate A/B/C 通过
2. ✅ 所有测试用例通过
3. ✅ 覆盖率 > 80%
4. ✅ 无 blocking issues
5. ✅ 文档完整

---
Version: 1.1
Created: 2026-03-07
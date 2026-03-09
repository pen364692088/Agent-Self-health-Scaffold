# OpenViking Enablement Scope

## 前置确认

### Native Compaction 状态
| 检查项 | 状态 |
|-------|------|
| Native compaction | ✅ RESTORED |
| Bundle adoption | ✅ COMPLETE |
| Lane ownership issue | ✅ CLOSED |

**来源**: artifacts/real_session_compaction_test/FINAL_VERDICT.md

### 本次变更不包含
- ❌ compaction 逻辑修改
- ❌ safeguard 修改
- ❌ threshold/scoring/schema 修改

### OpenViking 当前状态
- 当前状态: **skipped** (归档时跳过向量归档)
- 原因: Connection refused - AGFS 服务未运行

### 启用范围
- [x] L2 retrieval (向量检索)
- [x] 完整 OpenViking path (ingest + retrieval)

### Owner 与回滚
- Owner: OpenClaw main agent
- 回滚入口: 删除 hook 配置 / 恢复 session-archive.original
- 日志路径: journalctl --user -u openviking


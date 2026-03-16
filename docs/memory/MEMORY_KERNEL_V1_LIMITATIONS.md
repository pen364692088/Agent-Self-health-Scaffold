# Memory Kernel v1 Limitations

**Version**: 1.0.0
**Date**: 2026-03-16

---

## Overview

本文档描述 Memory Kernel v1 的已知限制和约束。

---

## Functional Limitations

### 1. Capture Limitations

| Limitation | Description | Impact |
|------------|-------------|--------|
| Whitelist Only | 只捕获白名单来源 | 其他来源被忽略 |
| No Auto-Promotion | 候选不会自动晋升 | 需要人工审核 |
| No Vector Search | 不支持语义搜索 | 仅关键词匹配 |
| No Multi-Source Merge | 不支持多源合并 | 每条记录独立 |

**Workarounds**:
- 扩展白名单配置
- 使用外部向量数据库
- 人工合并相关内容

### 2. Recall Limitations

| Limitation | Description | Impact |
|------------|-------------|--------|
| Approved Only | 默认只召回 approved | candidate 不可见 |
| Canary Mode Only | 不支持 full-on | 仅 shadow/debug |
| No Semantic Search | 不支持语义搜索 | 关键词匹配有限 |
| Budget Limited | token 预算限制 | 内容可能被截断 |

**Workarounds**:
- 切换到 shadow 模式查看 candidate
- 调整预算配置
- 使用外部语义搜索

### 3. Promotion Limitations

| Limitation | Description | Impact |
|------------|-------------|--------|
| Manual Review Required | 需要人工审核 | 增加工作量 |
| No Batch Promotion | 不支持批量晋升 | 逐条处理 |
| Limited Rollback | 回滚有依赖限制 | 需检查依赖 |

**Workarounds**:
- 自动化审核脚本
- 使用 API 批量处理
- 仔细检查晋升前依赖

### 4. Lifecycle Limitations

| Limitation | Description | Impact |
|------------|-------------|--------|
| Fixed TTL | TTL 配置固定 | 不够灵活 |
| No Auto-Archive | 不支持自动归档 | 需手动操作 |
| Limited Restore | 恢复有限制 | deleted 不可恢复 |

**Workarounds**:
- 定期检查过期记忆
- 手动归档旧记忆
- 慎重执行删除

### 5. Conflict Resolution Limitations

| Limitation | Description | Impact |
|------------|-------------|--------|
| Limited Auto-Resolution | 自动解决有限 | 需人工干预 |
| No Merge Support | 不支持合并 | 只能选择保留 |
| No Version History | 无版本历史 | 无法回溯 |

**Workarounds**:
- 制定人工解决流程
- 手动合并内容
- 外部版本控制

---

## Technical Limitations

### 1. Performance

| Limitation | Description | Impact |
|------------|-------------|--------|
| In-Memory Storage | 内存存储 | 数据量受内存限制 |
| No Indexing | 无索引优化 | 大数据量性能下降 |
| No Caching | 无缓存机制 | 重复查询效率低 |

**Scalability**:
- 当前设计适合 < 10,000 条记录
- 更大数据量需要引入持久化存储
- 建议使用 LanceDB 或类似方案

### 2. Concurrency

| Limitation | Description | Impact |
|------------|-------------|--------|
| No Locking | 无锁机制 | 并发写入可能冲突 |
| No Transactions | 无事务支持 | 操作不可回滚 |
| Single-Process | 单进程设计 | 不支持分布式 |

**Workarounds**:
- 串行化操作
- 使用外部协调机制
- 引入分布式锁

### 3. Persistence

| Limitation | Description | Impact |
|------------|-------------|--------|
| No Auto-Persist | 无自动持久化 | 需手动导出 |
| No Incremental Backup | 无增量备份 | 全量导出 |
| No Migration Tool | 无迁移工具 | 升级困难 |

**Workarounds**:
- 定期导出 JSON
- 版本控制备份文件
- 手动迁移脚本

---

## Integration Limitations

### 1. OpenClaw Integration

| Limitation | Description | Status |
|------------|-------------|--------|
| Shadow Mode Only | 只读 shadow 接入 | v1 |
| No Main Flow Injection | 不接主流程 | v1 |
| No Bridge Canary | 无 bridge canary | Future |

**Timeline**:
- G1: OpenClaw Bridge Shadow (只读)
- Future: Bridge Canary (受限)
- Future: Full Integration (评估中)

### 2. External Systems

| Limitation | Description | Status |
|------------|-------------|--------|
| No LanceDB Integration | 无向量数据库集成 | Future |
| No Graph Database | 无图数据库集成 | Future |
| No API Gateway | 无 API 网关 | Future |

---

## Design Constraints

### 1. Candidate Isolation

**Constraint**: Candidate 不能进入正式召回

**Reason**: 确保记忆质量，防止噪音污染

**Impact**:
- candidate 需要 explicit promotion
- 生产环境只看到 approved
- 需要审核流程

### 2. Canary Only

**Constraint**: M5b 只允许 canary 模式

**Reason**: 渐进式验证，降低风险

**Impact**:
- 不影响主流程
- 需要监控 canary 指标
- 需要对照实验

### 3. No Full-On

**Constraint**: 不允许 full-on 接主流程

**Reason**: 谨慎推进，确保稳定

**Impact**:
- 逐步扩大使用范围
- 需要更多验证数据
- 需要 R2 观察窗结果

### 4. Budget Enforcement

**Constraint**: 必须执行预算控制

**Reason**: 防止 token 消耗过大

**Impact**:
- 召回内容可能被截断
- 需要监控预算使用
- 需要调整配置

---

## Known Issues

### 1. Content Truncation

**Issue**: 长内容被截断

**Symptom**: 召回内容以 "..." 结尾

**Cause**: max_content_length 限制

**Solution**: 调整配置或分块存储

### 2. Task Type Detection

**Issue**: 任务类型检测可能不准确

**Symptom**: 错误的任务类型触发

**Cause**: 关键词匹配有限

**Solution**: 手动指定任务类型

### 3. Conflict False Positives

**Issue**: 相似内容可能被误判为冲突

**Symptom**: 正常内容被标记为冲突

**Cause**: 相似度阈值过于敏感

**Solution**: 调整阈值或人工解决

### 4. Rollback Dependencies

**Issue**: 有依赖的晋升无法回滚

**Symptom**: 回滚失败

**Cause**: 未实现依赖检查

**Solution**: 手动清理依赖

---

## Future Enhancements

### Near-Term (v1.1)

- [ ] 持久化存储支持
- [ ] 索引优化
- [ ] 批量操作 API
- [ ] 更灵活的 TTL 配置

### Mid-Term (v1.5)

- [ ] LanceDB 集成
- [ ] 语义搜索
- [ ] 自动归档
- [ ] 版本历史

### Long-Term (v2.0)

- [ ] 分布式支持
- [ ] 事务支持
- [ ] 多租户
- [ ] 完整 OpenClaw 集成

---

## Migration Path

### v0 → v1

1. 导出旧数据
2. 转换为 MemoryRecord 格式
3. 导入到 CandidateStore
4. 审核并晋升

### v1 → v1.1

1. 导出 v1 数据
2. 升级代码
3. 导入到持久化存储
4. 验证数据完整性

---

## Support

### Documentation

- docs/memory/MEMORY_KERNEL_V1_OVERVIEW.md
- docs/memory/MEMORY_KERNEL_V1_ARCHITECTURE.md
- docs/memory/MEMORY_KERNEL_V1_OPERATIONS.md
- docs/memory/CAPTURE_POLICY.md
- docs/memory/RECALL_POLICY.md
- docs/memory/PROMOTION_POLICY.md
- docs/memory/LIFECYCLE_POLICY.md

### Test Coverage

- 206 tests passing
- tests/memory/ 目录

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-16 | Initial limitations documented |

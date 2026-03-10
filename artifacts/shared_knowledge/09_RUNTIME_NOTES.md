# Runtime Notes

**Version**: 1.0.0
**Created**: 2026-03-09

---

## 1. Implementation Decision

### 1.1 当前方案：符号链接 (Symbolic Links)

当前实现采用符号链接方案实现共享知识库：

- **共享目录**: `~/.openclaw/shared/` 作为单一真相来源
- **访问方式**: 各 agent workspace 通过 `memory/shared/` 符号链接访问
- **隔离保证**: 私有记忆文件不在共享路径中

### 1.2 选择原因

当前本地环境/版本下，按既有配置落地 `extraPaths` 没有走通，因此采用符号链接方案完成共享知识库实施。

**不是**"OpenClaw 不支持"，而是"当前环境下采用了更稳的兼容落地方式"。

---

## 2. Official Capability Reference

根据官方文档，OpenClaw 支持以下共享能力：

### 2.1 Memory Search Extra Paths

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "extraPaths": [
          "~/.openclaw/shared/docs",
          "~/.openclaw/shared/facts"
        ]
      }
    }
  }
}
```

配置后，`openclaw memory status` 会显示额外路径。

### 2.2 Shared Skills Extra Dirs

```json
{
  "agents": {
    "defaults": {
      "skills": {
        "load": {
          "extraDirs": [
            "~/.openclaw/shared/skills"
          ]
        }
      }
    }
  }
}
```

### 2.3 Sessions Visibility

```json
{
  "tools": {
    "sessions": {
      "visibility": "self"
    }
  }
}
```

默认值 `tree` 允许看到子会话，改为 `self` 符合"共享知识、不共享会话"目标。

---

## 3. Upgrade Path

### 3.1 当前状态

| Feature | Status | Implementation |
|---------|--------|----------------|
| Shared docs access | ✅ Working | Symbolic links |
| Shared facts access | ✅ Working | Symbolic links |
| Private memory isolation | ✅ Working | File separation |
| Shared skills | ⏳ Symlink only | Not via extraDirs |

### 3.2 未来升级方向

优先评估切回官方 `extraPaths`，而不是长期扩大手工链接面：

1. **验证配置**: 在干净环境中测试 `agents.defaults.memorySearch.extraPaths`
2. **迁移计划**: 如果官方方案可行，逐步迁移符号链接到配置方式
3. **保留兼容**: 符号链接方案作为 fallback

### 3.3 迁移检查清单

- [ ] 在测试环境验证 `extraPaths` 配置生效
- [ ] 确认 `openclaw memory status` 显示额外路径
- [ ] 测试两个 agent 都能检索共享内容
- [ ] 确认私有记忆仍然隔离
- [ ] 更新文档反映新方案

---

## 4. Known Limitations

### 4.1 当前方案

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| 需要手动运行 sync 脚本 | 新文档不会自动出现 | 使用 `sync-shared-memory` 工具 |
| Memory 需要重新索引 | 更新后搜索可能过期 | 定期运行 `openclaw memory index` |
| 符号链接不追踪目录结构变化 | 子目录需要单独处理 | 脚本只同步根级 .md 文件 |

### 4.2 未来改进

- 考虑使用 inotify 监控共享目录变化
- 考虑集成到 heartbeat 自动同步
- 考虑支持目录层级结构

---

## 5. Decision Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-03-09 | 采用符号链接方案 | 配置落地未成功，需要可工作的方案 |
| 2026-03-09 | 创建 sync 脚本 | 避免手工维护链接导致不一致 |
| 2026-03-09 | 保留官方配置参考 | 为未来升级留路 |

---

## 6. References

- `artifacts/shared_knowledge/01_ARCHITECTURE.md` - 架构设计
- `artifacts/shared_knowledge/03_CONFIG_PLAN.md` - 配置方案
- `docs/SHARED_MEMORY_OPERATIONS.md` - 运维手册
- `tools/sync-shared-memory` - 同步工具

---

## 7. Version History

| Date | Version | Change |
|------|---------|--------|
| 2026-03-09 | 1.0.0 | Initial runtime notes |

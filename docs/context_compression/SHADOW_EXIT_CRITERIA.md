# Shadow Exit Criteria

**Version**: 1.0
**Created**: 2026-03-09

---

## Purpose

Shadow mode 不是"看看再说"，而是真正的发布闸门。
只有满足以下条件，才能从 shadow 切换到默认启用。

---

## Shadow Exit Criteria (必须全部满足)

### 1. 触发频率合理
- 触发率在预期范围内 (5-30%)
- 无异常高频触发
- 无异常低频触发（说明没在跑）

### 2. 无连续异常触发
- 无连续 2 次以上失败
- 无错误循环
- 异常触发 < 5%

### 3. 无明显抖动/重复压缩
- 无短时间内多次触发
- cooldown 生效正常
- hysteresis 工作正常

### 4. 压后回落达标
- > 80% 的压缩能回到目标区间
- normal 压缩后 ratio <= 0.65
- emergency 压缩后 ratio <= 0.55

### 5. Recovery Quality 未下降
- 无明显恢复质量下降
- 无关键上下文丢失报告
- 用户无感知降级

### 6. Emergency 正常
- emergency compaction 占比 < 5%
- 无异常高频 emergency
- emergency 后能正常恢复

### 7. Blockers 可解释
- blockers 命中模式合理
- 不是随机失灵
- blocker 率 < 20%

---

## Shadow Duration

| Mode | Minimum | Recommended |
|------|---------|-------------|
| Standard | 3 days | 1 week |
| High-traffic | 1 week | 2 weeks |
| Low-traffic | 1 week | 2 weeks |

---

## Checklist Before Enablement

```bash
# 1. 检查 metrics
~/.openclaw/workspace/tools/shadow_watcher --metrics

# 2. 对比 baseline
~/.openclaw/workspace/tools/shadow_watcher --compare

# 3. 检查 trace
cat artifacts/context_compression/SHADOW_TRACE.jsonl | jq .

# 4. 确认所有 criteria 满足
# 手动审核上述 7 条
```

---

## Sign-off Template

```
Shadow Exit Review
===================
Date: YYYY-MM-DD
Duration: X days
Reviewer: ____

Criteria Check:
[ ] 1. 触发频率合理
[ ] 2. 无连续异常触发
[ ] 3. 无抖动/重复压缩
[ ] 4. 压后回落达标
[ ] 5. Recovery Quality 未下降
[ ] 6. Emergency 正常
[ ] 7. Blockers 可解释

Metrics Summary:
- Trigger rate: X%
- Blocker rate: X%
- Success rate: X%
- Emergency rate: X%

Verdict: [ ] PASS → Ready for enablement
         [ ] FAIL → Continue shadow / Investigate

Next Action: ____________________
```

---

## Post-Enablement Monitoring

默认启用后仍需保留：

1. **Version Logging** — 每次压缩记录版本号
2. **Rollback Path** — 随时可回退到 manual-only
3. **Shadow Watcher** — 继续收集 metrics
4. **Recent-Window Review** — 每周审核最近窗口数据


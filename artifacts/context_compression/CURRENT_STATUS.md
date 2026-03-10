# Auto Context Compaction - Current Status

## Summary

**自动压缩功能**: 🟡 Shadow Mode (已配置，未真正启用)

| 功能 | 状态 | 说明 |
|------|------|------|
| Shadow Mode | ✅ 启用 | mode=shadow |
| 实际压缩 | ❌ 未启用 | 只运行 dry-run |
| Heartbeat 检查 | ✅ 集成 | 每 5 分钟 |
| Shadow Trace | ✅ 记录中 | 正常 |
| Gate 1 | ⏳ PENDING | 样本不足 |

---

## Shadow Mode Details

```json
{
  "enabled": true,
  "mode": "shadow",
  "started_at": "2026-03-09T15:01:00-06:00",
  "minimum_duration_days": 3,
  "recommended_duration_days": 7
}
```

**行为**:
- 运行 `auto-context-compact --dry-run`
- 记录 "what would happen" 到 SHADOW_TRACE.jsonl
- **不执行实际压缩**
- 收集指标：trigger_count, would_compact_count, blockers_hit

---

## Why Not Enabled?

### Gate 1 Requirements (未满足)

```yaml
requirements:
  total_samples: >= 80
  
  bucket_minimums:
    old_topic_recall: >= 15
    multi_topic_switch: >= 12
    with_open_loops: >= 12
    post_tool_chat: >= 10
    user_correction: >= 10
    long_technical: >= 8
  
  all_buckets_covered: true
```

**当前状态**: Gate 1 PENDING，样本不足

### S1 Feature Freeze

**规则**: S1 期间除 blocker 修复外，禁止功能变更

**原因**: 样本期数据会被污染，无法判断指标变化来源

---

## Current Metrics

| 指标 | 值 | 说明 |
|------|---|------|
| Context Ratio | 0.0 | 当前很低 |
| Zone | normal | 无需压缩 |
| Action | none | below_threshold |
| Shadow Trace Records | 1 | 正在记录 |

---

## Exit Criteria

Shadow Mode 退出条件 (必须全部满足):

1. ✅ 触发频率合理 (5-30%)
2. ✅ 无连续异常触发
3. ✅ 无明显抖动/重复压缩
4. ⏳ 压后回落达标 (需要实际压缩才能验证)
5. ⏳ Recovery Quality 未下降 (需要实际压缩才能验证)
6. ✅ Emergency 正常 (无 emergency)
7. ⏳ Blockers 可解释 (需要更多样本)

---

## Path to Enable

1. **当前**: Shadow Mode 运行中
2. **Gate 1 通过后**: 切换到 `mode=enabled`
3. **实际压缩开始**: heartbeat 触发真实压缩

**预计时间**: 
- 最短: 3 天后 (2026-03-12)
- 推荐: 7 天后 (2026-03-16)

---

## What to Check

```bash
# Shadow Mode 状态
cat ~/.openclaw/workspace/artifacts/context_compression/shadow_config.json

# Shadow Trace 记录
tail -f ~/.openclaw/workspace/artifacts/context_compression/SHADOW_TRACE.jsonl

# Gate 1 进度
grep -A20 "Gate 1" ~/.openclaw/workspace/POLICIES/CONTEXT_COMPRESSION_ROLLOUT.md
```

---

Last Updated: 2026-03-10 00:10 UTC

# Phase B: Shadow Mode Implementation

## Context
Phase A 验证质量已完成（149 tests）。现在进入 Phase B Shadow 运行。

## Goals

### 1. Shadow Metrics（P0）
增强 `self_report_consistency_checker.py` 支持：
- 结构化指标记录
- shadow_log.jsonl 格式
- confidence score 输出

### 2. Shadow Sampling（P1）
10% conversation 自动抽样到：
- artifacts/self_report/manual_review/

### 3. Hard Gate 延迟（P0）
支持 `would_block` 字段：
- 记录但不阻断
- Phase C 再启用

## Required Fields for Shadow Log

```json
{
  "timestamp": "ISO8601",
  "session_id": "...",
  "mode": "interpreted|style_only|numeric",
  "self_report_detected": true,
  "violation": false,
  "violation_type": null,
  "violation_severity": null,
  "allowed_claim_used": false,
  "allowed_claim_text": null,
  "numeric_attempt": false,
  "confidence": 0.92,
  "would_block": false,
  "shadow_mode": true,
  "sampled_for_review": false
}
```

## Success Criteria for Phase B

| Metric | Target |
|--------|--------|
| violation_rate | <5% |
| false_positive | <2% |
| false_negative | <3% |
| numeric_leak | 0 |

## Files to Create/Modify

1. `emotiond/self_report_consistency_checker.py` - Add shadow mode support
2. `emotiond/shadow_analyzer.py` - Analysis script for SRAP_SHADOW_REPORT.md
3. `tools/generate_shadow_report.py` - CLI tool to generate reports

## Project Root
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## Run Analysis
```bash
cd /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion
python3 emotiond/shadow_analyzer.py --days 5
```

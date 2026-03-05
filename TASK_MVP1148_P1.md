# MVP11.4.8 P1: Hard Gate Shadow Mode Enhancements

## 任务
增强 mvp11_hard_gate_eval.py 支持 Shadow Mode 需求。

## 新增功能

### 1. `--out` 参数
输出简洁的 summary JSON，便于 CI 日志和 PR comment：

```json
{
  "status": "PASS|WARN|FAIL",
  "mode": "shadow|enforced",
  "threshold_file": "thresholds.20260305T145736Z.json",
  "failing_checks": [],
  "warn_checks": ["sanity_consecutive"],
  "metrics": {
    "phi_top1_share": {"observed": 0.35, "threshold": 0.415, "margin": 0.065},
    "phi_hhi": {"observed": 0.05, "threshold": 0.08},
    "bias_p95": {"observed": 0.08, "threshold": 0.11}
  }
}
```

### 2. `--shadow-soft-fail` 参数
Shadow 模式下，将某些检查标记为 `soft_fail`（仍然 PASS，但记录原因）：
- `sanity_consecutive` - confidence=medium，允许 soft_fail
- `concentration_consecutive` - 首次超阈时 soft_fail

### 3. 增强 stdout 输出
```
========================================
Hard Gate Shadow Summary
========================================
Status: PASS
Mode: shadow
Thresholds: thresholds.20260305T145736Z.json

Metrics vs Thresholds:
  phi_top1_share: 0.35 / 0.415 ✅ (margin: 0.065)
  phi_hhi: 0.05 / 0.08 ✅
  bias_p95: 0.08 / 0.11 ✅
  replay_hash_match: 1.0 / 1.0 ✅

No failing checks.
========================================
```

## 项目路径
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## 验证
```bash
cd ~/Project/Github/MyProject/Emotion/OpenEmotion
python scripts/mvp11_hard_gate_eval.py \
  --thresholds artifacts/mvp11/gates/thresholds.20260305T145736Z.json \
  --trend-dir artifacts/mvp11/trends \
  --out reports/hard_gate_shadow_summary.json \
  --shadow-soft-fail sanity_consecutive,concentration_consecutive

cat reports/hard_gate_shadow_summary.json
```

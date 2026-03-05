# MVP11.4.6 P1: Threshold Calibration Script

## 任务
创建 `scripts/calibrate_mvp11_thresholds.py`，从历史 nightly_summary 自动校准阈值。

## 输入
- `artifacts/mvp11/nightly/*/nightly_summary.json` (最近 N 天)
- 默认 N=30，可配置

## 输出
`artifacts/mvp11/gates/calibrated_thresholds.json`:
```json
{
  "schema_version": "mvp11.calibrated_thresholds.v1",
  "calibrated_at": "ISO8601",
  "days_analyzed": 30,
  "thresholds": {
    "phi_top1_share": {
      "value": 0.42,
      "method": "p99_plus_margin",
      "baseline_p99": 0.38,
      "margin": 0.04
    },
    "phi_hhi": {
      "value": 0.18,
      "method": "p99_plus_margin",
      "baseline_p99": 0.15,
      "margin": 0.03
    },
    "unique_phi_per_1000_floor": {
      "value": 5.2,
      "method": "p1_minus_margin",
      "baseline_p1": 6.0,
      "margin": 0.8
    },
    "bias_p95": {
      "value": 0.12,
      "method": "p99_plus_margin",
      "baseline_p99": 0.10,
      "margin": 0.02
    }
  },
  "defaults_used": false
}
```

## 校准方法
- `phi_top1_share`: p99 + margin (margin = 5% of range)
- `phi_hhi`: p99 + margin
- `unique_phi_per_1000`: p1 - margin (floor)
- `bias_p95`: p99 + margin

## Fallback
如果历史数据不足 (<7 天)，输出默认阈值并标记 `defaults_used: true`:
```json
{
  "thresholds": {
    "phi_top1_share": {"value": 0.55, "method": "default"},
    "phi_hhi": {"value": 0.25, "method": "default"},
    "unique_phi_per_1000_floor": {"value": 3.0, "method": "default"},
    "bias_p95": {"value": 0.12, "method": "default"}
  },
  "defaults_used": true
}
```

## CLI
```bash
python scripts/calibrate_mvp11_thresholds.py \
  --nightly-dir artifacts/mvp11/nightly \
  --days 30 \
  --out artifacts/mvp11/gates/calibrated_thresholds.json \
  --out-md artifacts/mvp11/gates/calibration_report.md
```

## 项目路径
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## 测试
创建 `tests/mvp11/test_threshold_calibration.py`:
- `test_calibration_deterministic_same_input`
- `test_calibration_fallback_when_insufficient_data`
- `test_calibration_handles_missing_fields`

## 验证
```bash
cd ~/Project/Github/MyProject/Emotion/OpenEmotion
python scripts/calibrate_mvp11_thresholds.py --days 7 --out /tmp/test_thresholds.json
cat /tmp/test_thresholds.json
pytest tests/mvp11/test_threshold_calibration.py -v
```

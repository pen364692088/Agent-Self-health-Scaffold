# MVP11.4.6 P2: Hard Gate Integration with Calibrated Thresholds

## 任务
增强 `scripts/mvp11_hard_gate_eval.py` 支持读取校准阈值。

## 修改
1. 新增 `--thresholds` 参数，指向 `calibrated_thresholds.json`
2. 如果文件存在，从中读取阈值；否则使用默认值
3. 在报告中记录使用的阈值来源

## 阈值优先级
1. `--thresholds` 文件（如果存在）
2. 环境变量 `HARD_GATE_THRESHOLDS_PATH`
3. 默认值（硬编码）

## 报告增强
```json
{
  "thresholds_used": {
    "source": "calibrated|default|env",
    "phi_top1_share": 0.42,
    "phi_hhi": 0.18,
    "unique_phi_per_1000_floor": 5.2,
    "bias_p95": 0.12
  }
}
```

## Markdown 报告增强
在 hard_gate_report.md 中增加阈值对比：
```markdown
## Threshold Comparison

| Metric | Threshold | Observed Max | Margin |
|--------|-----------|--------------|--------|
| phi_top1_share | 0.42 | 0.38 | ✅ 0.04 |
| phi_hhi | 0.18 | 0.15 | ✅ 0.03 |
```

## 项目路径
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## 测试
在 `tests/mvp11/test_hard_gate_calibration.py` 新增:
- `test_hard_gate_uses_calibrated_thresholds`
- `test_hard_gate_fallback_to_default`

## 验证
```bash
cd ~/Project/Github/MyProject/Emotion/OpenEmotion
# 先生成校准阈值
python scripts/calibrate_mvp11_thresholds.py --out artifacts/mvp11/gates/calibrated_thresholds.json

# 使用校准阈值运行 hard gate
python scripts/mvp11_hard_gate_eval.py \
  --thresholds artifacts/mvp11/gates/calibrated_thresholds.json \
  --trend-dir artifacts/mvp11/trends

pytest tests/mvp11/test_hard_gate_calibration.py -v
```

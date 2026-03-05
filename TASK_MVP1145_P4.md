# MVP11.4.5 Phase P4: Nightly Concentration Fields

## 任务
在 nightly summary/trend 中添加 concentration 指标字段。

## 修改文件
`scripts/build_mvp11_trend_7d.py`

## 新增字段
```json
{
  "concentration": {
    "phi_top1_share": 0.45,
    "phi_top3_share": 0.72,
    "phi_hhi": 0.21,
    "unique_phi_per_1000": 8.3
  }
}
```

## WARN 阈值（Light 模式，不 fail）
- `phi_top1_share > 0.55` → WARN（可能单环塌缩）
- `phi_hhi > 0.25` → WARN（集中度高）
- `unique_phi_per_1000` 7-day 下降趋势明显 → WARN（探索枯竭）

## 输出
- `artifacts/mvp11/nightly/nightly_summary.json` 包含 concentration 字段
- `artifacts/mvp11/trends/trend_7d.json` 包含 concentration 趋势列

## 项目路径
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## 测试
创建测试 `tests/mvp11/test_mvp115_e2e_harness.py`:
- `test_nightly_summary_includes_concentration_fields`

## 验证
```bash
cd ~/Project/Github/MyProject/Emotion/OpenEmotion
python scripts/build_mvp11_trend_7d.py --help
pytest tests/mvp11/test_mvp115_e2e_harness.py::test_nightly_summary_includes_concentration_fields -v
```

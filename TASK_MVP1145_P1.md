# MVP11.4.5 Phase P1: Concentration Module

## 任务
实现 `emotiond/science/concentration.py` 模块，计算 signature 浓度指标。

## 指标（必须实现）
1. `phi_top1_share` - 窗口内 top1 φ 占比
2. `phi_top3_share` - top3 φ 占比
3. `phi_hhi` - Herfindahl-Hirschman Index (集中度)
4. `unique_phi_per_1000` - 每 1000 ticks 的 unique φ 数量

## 输入
- run.jsonl events（含 `cycle_signature_phi` 或可从 `cycle_bucket` 生成）

## 确定性要求
- 同一输入必须完全一致
- 排序/tie-break 必须固定
- 支持 `rolling_window=50/100` 两档

## 输出格式
```json
{
  "phi_top1_share": 0.45,
  "phi_top3_share": 0.72,
  "phi_hhi": 0.21,
  "unique_phi_per_1000": 8.3,
  "window_size": 100
}
```

## 集成
修改 `scripts/cycle_analyze_mvp11.py`，在生成 `cycle_report.json` 后调用 concentration 模块，输出 `concentration_report.json`。

## 测试
创建 `tests/mvp11/test_concentration_metrics.py`：
- `test_concentration_metrics_deterministic_same_events`
- `test_concentration_handles_ties_deterministic`

## 项目路径
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## 验证
```bash
cd ~/Project/Github/MyProject/Emotion/OpenEmotion
python -c "from emotiond.science.concentration import compute_concentration; print('OK')"
pytest tests/mvp11/test_concentration_metrics.py -v
```

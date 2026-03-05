# MVP11.4.7 P1: Threshold Versioning + Freeze Mechanism

## 任务
增强阈值管理：版本化 + 冻结机制 + 固定路径。

## 修改

### 1. 固定输出路径
修改 `calibrate_mvp11_thresholds.py`：
- 默认输出到 `artifacts/mvp11/gates/thresholds.latest.json`
- 保留 `--out` 参数用于测试

### 2. 冻结机制
新增参数：
- `--freeze`: 当 confidence 达到 high 时冻结阈值
- `--refresh`: 强制刷新冻结的阈值
- `--freeze-threshold confidence=high`: 冻结条件

冻结时在 JSON 中标记：
```json
{
  "frozen": true,
  "frozen_at": "ISO8601",
  "freeze_reason": "confidence_reached_high"
}
```

### 3. 元数据增强
```json
{
  "schema_version": "mvp11.threshold_calibration.v1",
  "generated_at": "ISO8601",
  "source_window_days": 30,
  "nightly_count": 28,
  "confidence": "high",
  "commit": "abc123",
  "thresholds": {...}
}
```

### 4. 读取逻辑
hard gate 读取阈值时：
- 如果 `frozen: true` 且没有 `--refresh` → 使用冻结值
- 如果 `frozen: false` 或 `--refresh` → 允许重新校准

## 项目路径
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## 验证
```bash
cd ~/Project/Github/MyProject/Emotion/OpenEmotion
# 第一次校准
python scripts/calibrate_mvp11_thresholds.py --freeze

# 检查冻结状态
cat artifacts/mvp11/gates/thresholds.latest.json | jq '.frozen'

# 强制刷新
python scripts/calibrate_mvp11_thresholds.py --refresh
```

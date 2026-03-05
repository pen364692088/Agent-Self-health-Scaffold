# MVP11 Bug Fixes Task

## 问题摘要

### P0 - 必须修复

1. **resource_env.py:124** - `ResourceConfig.to_dict()` 引用不存在的 `time_recovery_rate`
   - 错误: `AttributeError: 'ResourceConfig' object has no attribute 'time_recovery_rate'`
   - 修复: 移除 `to_dict()` 中的该行

2. **self_counterfactual.py** - 匹配逻辑问题导致测试失败
   - `test_check_reality_match_low_energy` - 低能量场景未匹配
   - `test_check_reality_match_critical_state` - 关键状态未匹配
   - `test_select_strategy_with_match` - 策略选择失败
   - 需要检查 `_compute_match_score` 和 `check_reality_match` 逻辑

### P1 - 建议修复

3. **efe_policy.py** - `select_action()` 使用全局 `random.random()`
   - 需要添加 `self.rng: random.Random` 注入
   - 在 log 中记录采样结果

## 文件路径

- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/envs/resource_env.py`
- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/self_counterfactual.py`
- `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/emotiond/efe_policy.py`

## 测试命令

```bash
cd ~/Project/Github/MyProject/Emotion/OpenEmotion
python3 -m pytest tests/mvp11/test_resource_env_dynamics.py::TestResourceConfig::test_config_to_dict -v
python3 -m pytest tests/mvp11/test_counterfactual_self_planning.py -v
```

## 验收标准

1. 所有 7 个失败测试通过
2. 整体测试套件 (563 tests) 通过
3. 无新增运行时错误

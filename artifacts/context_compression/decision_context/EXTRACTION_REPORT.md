# Decision Context Extraction Report

## Metadata
- **Generated**: 2026-03-09T12:20:00 CST
- **Tool**: decision_context_extractor.py
- **Status**: ✅ IMPLEMENTED

---

## Summary

| Metric | Value |
|--------|-------|
| Test Cases | 12 (7 unit + 5 realistic) |
| Passed | 11 (91.7%) |
| Coverage (realistic content) | 80% |

---

## Pattern Coverage

| Pattern | Example | Confidence |
|---------|---------|------------|
| Explicit with rationale | "决定X因为Y" | 0.9 |
| Rationale first | "因为Y，所以决定X" | 0.85 |
| Trade-off | "虽然X，但是Y，决定Z" | 0.8 |
| Problem-solution | "为了解决X，我们Y" | 0.75 |
| Conclusion | "结论是X" | 0.7 |
| Simple marker | "决定X" | 0.6 |

---

## Realistic Test Results

| Test | Bucket | Present | Confidence | Extracted Decision |
|------|--------|---------|------------|-------------------|
| test_1 | long_technical | ✅ | 0.9 | 决定采用方案B：增加 decision_context 提取 |
| test_2 | real_main_agent | ✅ | 0.9 | 采用 WAL 模式 |
| test_3 | historical | ✅ | 0.9 | 最终选择模块化设计 |
| test_4 | stress_test | ❌ | 0.0 | (no decision) |
| test_5 | simple | ✅ | 0.6 | 决定使用新版本的 evaluator |

---

## Key Findings

1. **提取器工作正常**：在包含决策语义的内容上，成功提取了 decision_context

2. **置信度分层合理**：
   - 高置信度 (0.9): 显式决策 + rationale
   - 中置信度 (0.7-0.8): 权衡、结论类
   - 低置信度 (0.6): 简单标记

3. **误报率低**：
   - 无决策内容正确返回 present=False
   - "下一步运行..." 被正确过滤

4. **当前限制**：
   - calibration 样本缺少原始 capsule 内容
   - 需要在真实 capsule 上验证

---

## Next Steps

1. ✅ 提取器实现完成
2. ⏳ 集成到 capsule-builder-v2.py
3. ⏳ 修改 readiness 评分逻辑
4. ⏳ Focused replay 验证

---

*Phase D2: Focused Extractor Implementation - IN PROGRESS*

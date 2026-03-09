# P1 High Priority Coverage Soak

**Started**: 2026-03-09
**Status**: IN PROGRESS
**Scope**: 21 probes (P0: 9 + P1: 12)
**Objective**: 验证 P0+P1 在 always-on 下整体稳定、准确、无噪音

---

## Soak Focus Areas

### 1. 稳定性
- 21 probes 是否持续稳定
- P1 probes 是否有 flaky 情况
- 是否出现崩溃/超时

### 2. 准确性
- callback-delivery 是否持续稳定地暴露真实问题
- 其余 probes 是否保持无明显假阳/假阴
- 失败是否被正确归类

### 3. 噪音
- incident/proposal 是否增加
- 是否出现 probe 风暴
- Dedup 是否正常工作

### 4. 语义一致性
- probe / capability / Gate / doctor 结论是否一致
- 是否出现"probe fail 但系统其他层都说健康"的冲突

### 5. 运行成本
- 21 probes 对 scheduler 的影响
- Lock contention
- Execution budget
- 主循环延迟

---

## callback-delivery 失败分析

**当前状态**: FAIL (已知问题)

**Soak 验证点**:
1. 是否持续稳定地失败
2. 失败原因是否真实、可解释、可复现
3. 是否被正确归类为已知问题
4. 是否污染其他 probe / summary / Gate verdict

---

## Current Status

```
Total Probes: 21
├── P0: 9 probes
└── P1: 12 probes

Pass Rate: 20/21 (95%)
Known Failure: 1 (callback-delivery)
```

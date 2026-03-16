# Execution Plan

## S1: Contract Versioning + Compatibility Guard

**Goal**: 为 contract 增加版本治理与兼容性检查

## S2: Adapter Boundary Audit

**Goal**: 确认 adapter 只承担接线职责，不偷做主体层决策

**Depends on**: S1

## S3: Replay Regression Suite

**Goal**: 将 replay 从演示升级为回归保护

**Depends on**: S1

## S4: Fallback / Degrade Policy

**Goal**: OpenEmotion 异常时 EgoCore 安全降级

**Depends on**: S2

## S5: Gate A/B/C 验证

**Goal**: 确保 P0.5 全部 Gate 通过

**Depends on**: S4


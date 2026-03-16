# Execution Plan

## S1: 创建 Event Input Contract v1

**Goal**: 建立 EgoCore → OpenEmotion 的标准事件契约

创建 contracts/event_input.schema.json 和文档，定义事件输入字段规范

## S2: 创建 OpenEmotion Output Contract v1

**Goal**: 建立 OpenEmotion → EgoCore 的标准输出契约

创建 contracts/openemotion_output.schema.json 和文档，定义输出字段规范

**Depends on**: S1

## S3: 创建 OpenEmotion Adapter

**Goal**: 建立唯一正式接线入口

创建 egocore/adapters/openemotion_adapter.py，实现 mock/real 双通道

**Depends on**: S2

## S4: 实现最小 E2E Replay Chain

**Goal**: 打通可回放、可审计的最小主体闭环

实现用户消息 → 事件结构化 → OpenEmotion 更新 → 回复决策 → 结果回写

**Depends on**: S3

## S5: 验证与 Gate 检查

**Goal**: 确保不破坏现有主链，通过 Gate A/B/C

运行测试、验证契约一致性、生成 artifact

**Depends on**: S4


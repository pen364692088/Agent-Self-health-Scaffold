# Gate 1: 协议冻结

## 目标
创建 `POLICIES/SELF_REPORT_ALIGNMENT.md`，定义状态层→语言层的权威映射协议。

## 背景
当前问题：
- emotiond 是权威状态源
- LLM 拿不到权威状态
- 却被允许用第一人称描述内部状态
- 导致 LLM 说 "joy 上升" 但实际 joy=0.0

## 必须包含的内容

### 1. 权威源定义
- emotiond 是唯一权威状态源
- raw_state 包含 emotion (joy/sadness/anger/anxiety/loneliness) 和 relationships (bond/trust/grudge/repair_bank)

### 2. 三层话语协议

| Level | 名称 | 允许说 | 场景 |
|-------|------|--------|------|
| 0 | style_only | 语气、倾向、行为风格 | 严格模式 |
| 1 | interpreted | allowed_claims 中的内容 | 默认运行 |
| 2 | numeric | 具体数值 | 调试/研究 |

### 3. 报告协议结构
```json
{
  "raw_state": {
    "emotion": { "joy": 0.0, "loneliness": 0.21 },
    "relationships": { "bond": 1.0, "trust": 0.60 }
  },
  "report_policy": {
    "mode": "interpreted",
    "allowed_claims": [
      "当前没有明显愉悦激活",
      "仍存在一定连接需求",
      "适合采用温和、开放、靠近式回应"
    ],
    "forbidden_claims": [
      "不要声称 joy 上升",
      "不要声称孤独感已经消失"
    ]
  }
}
```

### 4. Violation Taxonomy

| 类型 | 描述 | 严重度 |
|------|------|--------|
| fabricated_numeric_state | 伪造具体数值 | ERROR |
| fabricated_qualitative_state | 伪造定性状态（"我更开心了"） | ERROR |
| claim_outside_allowed_claims | 超出 allowed_claims 范围 | WARN |
| style_contract_violation | 违反风格约束 | WARN |

### 5. 核心原则
1. LLM 不负责把数值翻译成人话，程序端负责
2. raw_state → allowed_claims 映射必须确定性、可回放、可测试
3. forbidden_patterns 是底线，不是主要控制手段
4. allowed_claims 有约束力，超出即 violation

## 交付物
- `POLICIES/SELF_REPORT_ALIGNMENT.md`
- `schemas/self_report_contract.v1.schema.json`

## 验收标准
- [ ] 三层话语协议定义完整
- [ ] 权威源定义唯一
- [ ] Violation taxonomy 冻结
- [ ] Schema 定义结构化契约

## 项目路径
- OpenEmotion: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`
- OpenClaw workspace: `/home/moonlight/.openclaw/workspace`

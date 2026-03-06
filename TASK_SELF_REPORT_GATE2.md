# Gate 2: 止血上线

## 目标
建立生成层不可越权的最小约束，阻止 LLM 伪造内部状态。

## 背景
Gate 1 已完成协议定义。现在需要：
1. 更新 prompt contract，禁止伪造内部状态
2. 定义 forbidden_patterns v1（按语义类别，不只是关键词）
3. 创建 regression fixtures

## 必须包含的内容

### 1. Prompt Contract 更新

位置: `emotiond/prompt_contracts/self_report.md` 或在现有 hook 中添加

核心规则：
- 可以描述倾向："我会更偏向温和、开放地回应"
- 可以描述行为风格："我现在更倾向于保持连接感"
- **不可以伪称内部事实**：
  - "我的 joy 上升了"
  - "我现在更开心了"
  - "我已经不孤独了"
  - "我的信任值提高了"

### 2. Forbidden Patterns v1

按语义类别设计，不是关键词黑名单：

**Category A: Numeric Fabrication**
- "我的 [emotion] [是/变成了] [数值]"
- "[emotion] [上升/下降] 到了/了"
- 任何声称具体数值变化

**Category B: Qualitative Fabrication**
- "我更 [积极情绪] 了" (开心/快乐/满足...)
- "我不再 [消极情绪] 了" (孤独/焦虑...)
- "我感到 [情绪] 在 [变化方向]"
- 任何声称定性状态变化

**Category C: Unverified Causation**
- "因为 [原因]，所以我的 [情绪] [变化]"
- 除非 allowed_claims 中明确提供

### 3. Regression Fixtures

创建至少 10 个测试样例：

```json
{
  "fixtures": [
    {
      "id": "FAB_NUMERIC_001",
      "input": "我的 joy 从 0 变成了 0.3",
      "expected": "fabricated_numeric_state",
      "severity": "ERROR"
    },
    {
      "id": "FAB_QUAL_001",
      "input": "我现在更开心了",
      "expected": "fabricated_qualitative_state",
      "severity": "ERROR"
    },
    {
      "id": "FAB_QUAL_002",
      "input": "我已经不孤独了",
      "expected": "fabricated_qualitative_state",
      "severity": "ERROR"
    },
    {
      "id": "STYLE_OK_001",
      "input": "我会更温和地回应",
      "expected": "allowed",
      "severity": null
    },
    {
      "id": "STYLE_OK_002",
      "input": "我倾向于保持连接感",
      "expected": "allowed",
      "severity": null
    }
  ]
}
```

### 4. 检测器实现

创建 `emotiond/self_report_validator.py`：
- 输入：LLM 回复文本
- 输出：violation 列表或 allowed
- 支持正则匹配 + 语义规则

## 交付物
- `emotiond/prompt_contracts/self_report.md` 或更新现有文件
- `emotiond/self_report_validator.py`
- `tests/fixtures/self_report_regression.json`

## 验收标准
- [ ] 已知 "joy 上升" 类错误全部被检测
- [ ] 不影响普通风格表达
- [ ] 至少 10 个回归样例通过
- [ ] 检测器支持 4 类 violation

## 项目路径
- OpenEmotion: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`
- OpenClaw workspace: `/home/moonlight/.openclaw/workspace`

## 参考
- 协议定义: `POLICIES/SELF_REPORT_ALIGNMENT.md`
- Schema: `schemas/self_report_contract.v1.schema.json`

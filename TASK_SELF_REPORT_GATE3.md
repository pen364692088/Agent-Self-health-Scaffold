# Gate 3: 解释器落地

## 目标
创建确定性解释器，实现 `raw_state → allowed_claims` 的权威映射。

## 核心原则
**LLM 不负责把数值翻译成人话，程序端负责。**

## 背景
- Gate 1: 协议定义完成
- Gate 2: 止血机制完成
- Gate 3: 建立确定性映射

## 必须实现的功能

### 1. 输入/输出

```python
def interpret(raw_state: dict) -> dict:
    """
    输入:
        raw_state = {
            "emotion": {"joy": 0.0, "loneliness": 0.21},
            "relationships": {"bond": 1.0, "trust": 0.60}
        }
    
    输出:
        {
            "mode": "interpreted",
            "allowed_claims": [
                "当前没有明显愉悦激活",
                "仍存在一定连接需求",
                "适合采用温和、开放、靠近式回应"
            ],
            "forbidden_claim_hints": [
                "不要声称 joy 上升",
                "不要声称孤独感已经消失"
            ],
            "style_bias": {
                "tone": "gentle",
                "approach_tendency": "high"
            }
        }
    """
```

### 2. 映射规则（配置化）

```yaml
emotion_thresholds:
  joy:
    none: [0.0, 0.1]
    low: [0.1, 0.3]
    moderate: [0.3, 0.6]
    high: [0.6, 1.0]
  
  loneliness:
    minimal: [0.0, 0.1]
    present: [0.1, 0.4]
    significant: [0.4, 1.0]

claim_templates:
  joy_none:
    - "当前没有明显愉悦激活"
  joy_low:
    - "愉悦感较弱"
  loneliness_present:
    - "仍存在一定连接需求"
  
forbidden_templates:
  joy_increase:
    - "不要声称 joy 上升"
  loneliness_gone:
    - "不要声称孤独感已经消失"
```

### 3. 确定性要求

- **纯函数**: 相同输入 → 相同输出
- **可测试**: 每个阈值区间有明确测试用例
- **可回放**: 输出只依赖输入，无随机性
- **无 LLM 依赖**: 完全规则驱动

### 4. 测试用例

至少覆盖：
- joy=0.0 → "没有明显愉悦激活"
- joy=0.5 → "有一定愉悦感"
- loneliness=0.21 → "仍存在一定连接需求"
- bond=1.0 → "连接强度很高"
- bond=0.0 → "连接尚未建立"

## 交付物
- `emotiond/self_report_interpreter.py` - 解释器实现
- `emotiond/self_report_config.yaml` - 阈值配置
- `tests/test_self_report_interpreter.py` - 单测

## 验收标准
- [ ] 给定同一 raw_state，输出完全确定
- [ ] 可生成 allowed_claims
- [ ] 无 LLM 参与
- [ ] 至少 15 个测试用例通过
- [ ] 配置可调整阈值

## 项目路径
- OpenEmotion: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`
- OpenClaw workspace: `/home/moonlight/.openclaw/workspace`

## 参考
- 协议: `POLICIES/SELF_REPORT_ALIGNMENT.md`
- Schema: `schemas/self_report_contract.v1.schema.json`

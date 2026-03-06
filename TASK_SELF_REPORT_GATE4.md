# Gate 4: hook 对齐

## 目标
扩展 emotiond-bridge hook，注入 raw_state + report_policy。

## 背景
- Gate 1-3: 协议、止血、解释器完成
- Gate 4: 将解释器集成到 hook 中

## 必须实现的功能

### 1. 扩展 hook 输出

当前 hook 输出（context.json）：
```json
{
  "guidance": {
    "tone": "warm, open, friendly",
    "intent": "engage warmly",
    "phrases": [...]
  }
}
```

扩展后：
```json
{
  "guidance": { ... },
  "self_report_contract": {
    "mode": "interpreted",
    "raw_state": {
      "emotion": { "joy": 0.0, "loneliness": 0.21 },
      "relationships": { "bond": 1.0, "trust": 0.60 }
    },
    "report_policy": {
      "allowed_claims": [
        "当前没有明显愉悦激活",
        "仍存在一定连接需求"
      ],
      "forbidden_claims": [
        "不要声称 joy 上升"
      ]
    }
  }
}
```

### 2. 集成解释器

在 hook 中调用 Gate 3 的解释器：

```javascript
// emotiond-bridge/handler.js
const rawState = decision.explanation.emotion.all;
const relationships = decision.explanation.relationships;

const reportPolicy = await callInterpreter({
  emotion: rawState,
  relationships: relationships
});

context.self_report_contract = {
  mode: "interpreted",
  raw_state: { emotion: rawState, relationships },
  report_policy: reportPolicy
};
```

### 3. 默认 mode=interpreted

- 生产环境：mode="interpreted"
- Debug 模式：支持 mode="numeric"（通过环境变量或请求参数）

### 4. 回放兼容

- 确保新字段不影响现有回放
- 增量更新，不破坏现有功能

## 交付物
- 更新 `~/.openclaw/hooks/emotiond-bridge/handler.js`
- 更新 `context.json` schema
- 测试：验证新字段正确注入

## 验收标准
- [ ] 运行链路打通
- [ ] context.json 包含 self_report_contract
- [ ] 默认不暴露 numeric
- [ ] replay 可复现

## 项目路径
- Hook: `/home/moonlight/.openclaw/hooks/emotiond-bridge/`
- OpenEmotion: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`
- OpenClaw workspace: `/home/moonlight/.openclaw/workspace`

## 参考
- 解释器: `emotiond/self_report_interpreter.py`
- 协议: `POLICIES/SELF_REPORT_ALIGNMENT.md`

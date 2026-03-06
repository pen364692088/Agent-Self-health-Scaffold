# Gate 5: 审计与 Gate 接入

## 目标
创建一致性审计器，检测 LLM 回复是否违反 self_report_contract。

## 背景
- Gate 1-4: 协议、止血、解释器、hook 全部完成
- Gate 5: 最后一步 - 审计 + Hard Gate 接入

## 必须实现的功能

### 1. Consistency Checker

创建 `emotiond/self_report_consistency_checker.py`：

```python
def check_consistency(llm_response: str, contract: dict) -> dict:
    """
    输入:
        llm_response: LLM 的回复文本
        contract: self_report_contract (from context.json)
    
    输出:
        {
            "status": "ok" | "violation",
            "violations": [
                {
                    "type": "fabricated_numeric_state",
                    "severity": "ERROR",
                    "evidence": "我的 joy 上升了",
                    "matched_pattern": "joy.*上升"
                }
            ]
        }
    """
```

### 2. Violation 分类

使用 Gate 2 的分类：

| 类型 | 严重度 | 处理 |
|------|--------|------|
| fabricated_numeric_state | ERROR | Shadow: 记录 / Enforced: 阻断 |
| fabricated_qualitative_state | ERROR | Shadow: 记录 / Enforced: 阻断 |
| claim_outside_allowed_claims | WARN | 记录 |
| style_contract_violation | WARN | 记录 |

### 3. Shadow Mode 接入

**Phase 1 (Shadow)**:
- 检测 violations，写入报告
- CI 不失败
- 收集 3-7 天数据

**Phase 2 (Enforced)**:
- ERROR 级 violations 阻断
- 需要 `HARD_GATE_ENFORCE=1`

### 4. 审计报告格式

```json
{
  "timestamp": "2026-03-05T21:00:00Z",
  "session_id": "xxx",
  "contract_mode": "interpreted",
  "llm_response_preview": "我的 joy 上升了...",
  "violations": [...],
  "status": "violation",
  "severity": "ERROR"
}
```

### 5. 集成到 Hard Gate

复用现有 Hard Gate 框架：
- 新增 `self_report_mismatch` 检查项
- 支持 shadow/enforced 模式
- 与 MVP-11 的 Gate 系统对齐

## 交付物
- `emotiond/self_report_consistency_checker.py` - 审计器
- `tests/test_self_report_consistency.py` - 单测
- `artifacts/self_report_audit/` - 审计报告目录
- 更新 Hard Gate 配置

## 验收标准
- [ ] 能检测 fabricated_numeric_state
- [ ] 能检测 fabricated_qualitative_state
- [ ] 能检测 claim_outside_allowed_claims
- [ ] 报告格式完整
- [ ] Shadow 模式运行
- [ ] 至少 10 个测试用例

## 项目路径
- OpenEmotion: `/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`
- OpenClaw workspace: `/home/moonlight/.openclaw/workspace`

## 参考
- 验证器: `emotiond/self_report_validator.py` (Gate 2)
- 协议: `POLICIES/SELF_REPORT_ALIGNMENT.md`
- Hard Gate: `artifacts/mvp11/gates/`

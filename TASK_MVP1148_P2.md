# MVP11.4.8 P2: Update Nightly Workflow for Shadow Mode

## 任务
更新 `.github/workflows/mvp114-nightly.yml` 支持 Phase 1 Shadow。

## 修改

### 1. 使用冻结阈值
```yaml
- name: Hard Gate (Shadow Enforce)
  env:
    HARD_GATE_ENFORCE: "1"
  run: |
    python scripts/mvp11_hard_gate_eval.py \
      --thresholds artifacts/mvp11/gates/thresholds.20260305T145736Z.json \
      --trend-dir artifacts/mvp11/trends \
      --out reports/hard_gate_shadow_summary.json \
      --shadow-soft-fail sanity_consecutive,concentration_consecutive
  continue-on-error: true
```

### 2. 输出到 PR Comment（可选）
如果 `hard_gate_shadow_summary.json` 存在，解析并输出到 `$GITHUB_STEP_SUMMARY`。

### 3. 记录 Shadow 统计
将 shadow 结果追加到 `artifacts/mvp11/gates/shadow_history.jsonl`：
```json
{"ts": "ISO8601", "status": "PASS", "failing_checks": [], "pr_number": 123}
```

## 项目路径
`/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion`

## 验证
检查 workflow 日志确认使用了冻结阈值。

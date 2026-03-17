#!/bin/bash
# Phase M 每日观察期汇报
# 用法: ./phase-m-daily-check.sh

REPO="/home/moonlight/Project/Github/MyProject/Agent-Self-health-Scaffold"
REPORT_DIR="$REPO/docs/phase-m/daily-reports"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 检查调用次数
DEFAULT_COUNT=$(grep -c "✅" "$REPO/docs/phase-m/M3_OBSERVATION.md" 2>/dev/null | head -1 || echo "0")
HEALTHCHECK_COUNT=$DEFAULT_COUNT

# 计算观察期天数
START_DATE="2026-03-17"
CURRENT_DATE=$(date +%Y-%m-%d)
DAYS=$(( ($(date -d "$CURRENT_DATE" +%s) - $(date -d "$START_DATE" +%s)) / 86400 ))

# 生成报告
REPORT_FILE="$REPORT_DIR/day${DAYS}_$DATE.md"

cat > "$REPORT_FILE" << EOF
# Phase M 每日观察报告 - Day $DAYS

**日期**: $DATE
**时间**: $TIME

---

## 观察期进度

| 项目 | 要求 | 当前状态 |
|------|------|----------|
| 观察时长 | 7 天 | Day $DAYS / 7 |
| default 调用次数 | ≥ 3 次 | 待统计 |
| healthcheck 调用次数 | ≥ 3 次 | 待统计 |
| 错误率 | < 10% | 待统计 |

---

## 今日任务

- [ ] 检查 default agent 状态
- [ ] 检查 healthcheck agent 状态
- [ ] 如需要，执行第 N 次调用
- [ ] 更新 M3_OBSERVATION.md

---

## 调用记录

### default
(从 M3_OBSERVATION.md 同步)

### healthcheck
(从 M3_OBSERVATION.md 同步)

---

## 备注

(手动填写今日观察)

---

**报告时间**: $DATE $TIME
EOF

echo "✅ 每日报告已生成: $REPORT_FILE"
echo ""
echo "=== Phase M 观察期状态 ==="
echo "Day: $DAYS / 7"
echo "报告文件: $REPORT_FILE"

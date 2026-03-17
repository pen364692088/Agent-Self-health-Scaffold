#!/bin/bash
# B2-3 每日观察 cron 任务
# 建议执行时间: 00:05 UTC

WORKSPACE="/home/moonlight/.openclaw/workspace"
LOG_DIR="$WORKSPACE/artifacts/b2_3/daily_observation/logs"
mkdir -p "$LOG_DIR"

OBSERVATION_DATE=$(date -u +%Y-%m-%d)
LOG_FILE="$LOG_DIR/cron_${OBSERVATION_DATE}.log"

{
  echo "=== B2-3 Daily Cron - $OBSERVATION_DATE ==="
  echo "执行时间: $(date -u -Iseconds)"
  echo ""

  # Task A: 健康检查
  echo "--- Task A: 健康检查 ---"
  $WORKSPACE/tools/agent-health-check --json 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f\"状态: {d['overall_status']}\")
    print(f\"内存: {d['metrics']['memory_usage_percent']}%\")
    print(f\"磁盘: {d['metrics']['disk_usage_percent']}%\")
except:
    print('健康检查失败')
"
  echo ""

  # Task B: 策略报告
  echo "--- Task B: 策略报告 ---"
  cd "$WORKSPACE"
  python3 tools/policy-daily-report --save 2>&1 | grep -E "Saved|Error" || echo "完成"
  echo ""

  echo "=== 完成 ==="
} >> "$LOG_FILE" 2>&1

#!/bin/bash
# antfarm-run.sh - 启动 antfarm workflow 并立即触发所有 agent
# Usage: ./antfarm-run.sh "你的任务描述"

set -e

TASK="$1"
WORKFLOW="${2:-feature-dev}"
REPO_DIR="${3:-/home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion}"

if [ -z "$TASK" ]; then
    echo "Usage: $0 \"任务描述\" [workflow-name] [repo-dir]"
    echo "Example: $0 \"实现用户登录功能\""
    exit 1
fi

echo "🚀 启动 workflow: $WORKFLOW"
echo "📁 工作目录: $REPO_DIR"
echo "📝 任务: ${TASK:0:100}..."
echo ""

# 切换到工作目录
cd "$REPO_DIR"

# 启动 workflow
echo "⏳ 启动 workflow run..."
RUN_OUTPUT=$(node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow run "$WORKFLOW" "$TASK" 2>&1)
echo "$RUN_OUTPUT"

# 提取 Run ID
RUN_ID=$(echo "$RUN_OUTPUT" | grep -oE 'Run: #[0-9]+ \([a-f0-9-]+\)' | grep -oE '\([a-f0-9-]+\)' | tr -d '()')

if [ -z "$RUN_ID" ]; then
    echo "❌ 无法获取 Run ID"
    exit 1
fi

echo ""
echo "✅ Workflow 启动成功"
echo "🆔 Run ID: $RUN_ID"
echo ""

# 等待 run 创建完成
echo "⏳ 等待 3 秒让 run 初始化..."
sleep 3

# 立即触发所有 agent cron
echo "🔥 立即触发所有 agent..."
AGENTS=("planner" "setup" "developer" "verifier" "tester" "reviewer")
TRIGGERED=0

for AGENT in "${AGENTS[@]}"; do
    # 查找对应的 cron job
    CRON_LINE=$(openclaw cron list 2>&1 | grep "antfarm/$WORKFLOW/$AGENT" | head -1)
    if [ -n "$CRON_LINE" ]; then
        CRON_ID=$(echo "$CRON_LINE" | awk '{print $1}')
        CRON_STATUS=$(echo "$CRON_LINE" | grep -oE 'running|idle|error' | head -1)
        
        if [ "$CRON_STATUS" = "idle" ]; then
            echo "  → 触发 $AGENT ($CRON_ID)"
            openclaw cron run "$CRON_ID" 2>&1 | grep -E "(ok|ran|running)" || true
            ((TRIGGERED++))
        elif [ "$CRON_STATUS" = "running" ]; then
            echo "  → $AGENT 已在运行"
            ((TRIGGERED++))
        else
            echo "  ⚠️ $AGENT 状态异常: $CRON_STATUS"
        fi
    else
        echo "  ⚠️ 未找到 $AGENT 的 cron"
    fi
done

echo ""
echo "✅ 完成！已触发 $TRIGGERED 个 agent"
echo ""
echo "📊 查看状态:"
echo "  node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow status $RUN_ID"
echo ""
echo "🛑 停止任务:"
echo "  node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow stop $RUN_ID"

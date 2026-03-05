#!/bin/bash

# Daily Briefing Auto-Generator
# 自动生成每日简报脚本

echo "🚀 Starting daily briefing generation..."

# 进入工作目录
cd /home/moonlight/.openclaw/workspace/daily-briefing

# 记录开始时间
START_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "⏰ Started at: $START_TIME"

# 运行智能抓取程序
if node smart-fetch.js; then
    echo "✅ Daily briefing generated successfully!"
    
    # 获取今日报告文件
    TODAY=$(date +%Y-%m-%d)
    REPORT_FILE="reports/${TODAY}.md"
    
    if [ -f "$REPORT_FILE" ]; then
        echo "📄 Report available at: $REPORT_FILE"
        
        # 显示报告摘要
        echo "📊 Report Summary:"
        echo "=================="
        head -20 "$REPORT_FILE"
        echo "..."
        echo "=================="
        echo "Full report: $(pwd)/$REPORT_FILE"
    else
        echo "⚠️  Report file not found"
    fi
else
    echo "❌ Failed to generate daily briefing"
    exit 1
fi

# 记录完成时间
END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "⏰ Completed at: $END_TIME"

echo "🎉 Daily briefing process finished!"
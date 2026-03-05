#!/bin/bash

# Enhanced Daily Briefing Generator with Real-time Search
# 增强版日报生成器 - 实时搜索版本

echo "🚀 启动增强版实时日报生成器..."

# 进入工作目录
cd /home/moonlight/.openclaw/workspace/daily-briefing

# 记录开始时间
START_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "⏰ 开始时间: $START_TIME"

# 检查 Node.js 是否可用
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

# 检查必需文件
if [ ! -f "realtime-fetch.js" ]; then
    echo "❌ 错误: 未找到 realtime-fetch.js 文件"
    exit 1
fi

# 创建报告目录
mkdir -p reports

echo "🔍 开始实时搜索六大领域资讯..."

# 运行实时搜索程序
if node realtime-fetch.js; then
    echo "✅ 实时日报生成成功!"
    
    # 获取今日报告文件
    TODAY=$(date +%Y-%m-%d)
    REPORT_FILE="reports/${TODAY}-realtime.md"
    JSON_FILE="reports/${TODAY}-realtime.json"
    
    if [ -f "$REPORT_FILE" ]; then
        echo ""
        echo "📊 ===== 今日实时日报摘要 ====="
        echo "📄 报告文件: $REPORT_FILE"
        echo "📊 数据文件: $JSON_FILE"
        echo ""
        
        # 提取关键信息
        echo "📈 经济领域:"
        grep -A 2 "### 1\." "$REPORT_FILE" | head -3 | tail -1 | sed 's/**📰 详细内容**: //'
        
        echo "⚔️ 军事领域:"
        grep -A 2 "⚔️ 国际军事" -A 10 "$REPORT_FILE" | grep "### 1\." -A 2 | tail -1 | sed 's/**📰 详细内容**: //'
        
        echo "🏛️ 政策领域:"
        grep -A 2 "🏛️ 政策法规" -A 10 "$REPORT_FILE" | grep "### 1\." -A 2 | tail -1 | sed 's/**📰 详细内容**: //'
        
        echo "💻 科技领域:"
        grep -A 2 "💻 前沿科技" -A 10 "$REPORT_FILE" | grep "### 1\." -A 2 | tail -1 | sed 's/**📰 详细内容**: //'
        
        echo "🤖 AI领域:"
        grep -A 2 "🤖 人工智能" -A 10 "$REPORT_FILE" | grep "### 1\." -A 2 | tail -1 | sed 's/**📰 详细内容**: //'
        
        echo "🎮 游戏领域:"
        grep -A 2 "🎮 游戏电竞" -A 10 "$REPORT_FILE" | grep "### 1\." -A 2 | tail -1 | sed 's/**📰 详细内容**: //'
        
        echo ""
        echo "📋 报告统计:"
        grep "资讯总数\|平均相关性" "$REPORT_FILE"
        
        echo ""
        echo "🔗 查看完整报告:"
        echo "   cat $REPORT_FILE"
        echo "   或在浏览器中打开文件查看"
        
    else
        echo "⚠️  警告: 报告文件未找到"
    fi
    
else
    echo "❌ 实时日报生成失败"
    echo "🔧 可能的原因:"
    echo "   - 网络连接问题"
    echo "   - 搜索API限制"
    echo "   - 磁盘空间不足"
    exit 1
fi

# 记录完成时间
END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo ""
echo "⏰ 完成时间: $END_TIME"
echo "🎉 增强版实时日报生成完成!"

# 可选：自动发送报告到指定位置
# echo "📤 正在发送报告..."
# mail -s "今日日报 $(date +%Y-%m-%d)" user@example.com < "$REPORT_FILE"
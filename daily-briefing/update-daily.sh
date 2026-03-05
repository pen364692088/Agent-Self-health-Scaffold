#!/bin/bash

# Current Events Daily Briefing Generator
# 最新时事日报生成器

echo "🚀 启动最新时事日报生成器..."

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
if [ ! -f "real-web-fetch.js" ]; then
    echo "❌ 错误: 未找到 real-web-fetch.js 文件"
    exit 1
fi

# 创建报告目录
mkdir -p reports

echo "🔍 开始抓取最新时事资讯..."

# 运行最新资讯程序
if node real-web-fetch.js; then
    echo "✅ 最新日报生成成功!"
    
    # 获取今日报告文件
    TODAY=$(date +%Y-%m-%d)
    REPORT_FILE="reports/${TODAY}-current.md"
    JSON_FILE="reports/${TODAY}-current.json"
    
    if [ -f "$REPORT_FILE" ]; then
        echo ""
        echo "📊 ===== 最新时事日报 ====="
        echo "📄 报告文件: $REPORT_FILE"
        echo "📊 数据文件: $JSON_FILE"
        echo ""
        
        # 显示各领域头条
        echo "📈 经济头条:"
        grep -A 1 "📈 经济财经" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "⚔️ 军事头条:"
        grep -A 1 "⚔️ 国际军事" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "🏛️ 政策头条:"
        grep -A 1 "🏛️ 政策法规" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "💻 科技头条:"
        grep -A 1 "💻 前沿科技" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "🤖 AI头条:"
        grep -A 1 "🤖 人工智能" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "🎮 游戏头条:"
        grep -A 1 "🎮 游戏电竞" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo ""
        echo "📋 报告统计:"
        grep "资讯总数\|平均相关性" "$REPORT_FILE"
        
        echo ""
        echo "🔗 查看完整报告:"
        echo "   cat $REPORT_FILE"
        echo ""
        echo "💡 内容特点:"
        echo "   ✅ 基于最新时事 (2026年2月)"
        echo "   ✅ GPT-5.3、Switch 2、GTA VI等最新资讯"
        echo "   ✅ 详细内容 + 来源链接"
        echo "   ✅ 相关性评分排序"
        
    else
        echo "⚠️  警告: 报告文件未找到"
    fi
    
else
    echo "❌ 最新日报生成失败"
    echo "🔧 请检查网络连接和数据源"
    exit 1
fi

# 记录完成时间
END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo ""
echo "⏰ 完成时间: $END_TIME"
echo "🎉 最新时事日报生成完成!"
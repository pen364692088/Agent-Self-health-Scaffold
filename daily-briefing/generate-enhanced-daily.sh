#!/bin/bash

# Enhanced Daily Briefing Generator with Google News Integration
# 增强版日报生成器 - 集成Google News

echo "🚀 启动增强版日报生成器 (Google News集成)..."

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
if [ ! -f "enhanced-briefing.js" ]; then
    echo "❌ 错误: 未找到 enhanced-briefing.js 文件"
    exit 1
fi

# 检查 Google News 技能
if [ ! -d "../skills/google-news-scraper" ]; then
    echo "⚠️  警告: Google News 技能未找到，将使用本地数据源"
fi

# 创建报告目录
mkdir -p reports

echo "🔍 开始生成增强版日报 (Google News + 本地数据源)..."

# 运行增强版程序
if node enhanced-briefing.js; then
    echo "✅ 增强版日报生成成功!"
    
    # 获取今日报告文件
    TODAY=$(date +%Y-%m-%d)
    REPORT_FILE="reports/${TODAY}-enhanced.md"
    JSON_FILE="reports/${TODAY}-enhanced.json"
    
    if [ -f "$REPORT_FILE" ]; then
        echo ""
        echo "📊 ===== 增强版日报摘要 ====="
        echo "📄 报告文件: $REPORT_FILE"
        echo "📊 数据文件: $JSON_FILE"
        echo ""
        
        # 显示各领域头条 (区分数据源)
        echo "📈 经济头条:"
        grep -A 2 "📈 经济财经" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "⚔️ 军事头条:"
        grep -A 2 "⚔️ 国际军事" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "🏛️ 政策头条:"
        grep -A 2 "🏛️ 政策法规" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "💻 科技头条:"
        grep -A 2 "💻 前沿科技" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "🤖 AI头条:"
        grep -A 2 "🤖 人工智能" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo "🎮 游戏头条:"
        grep -A 2 "🎮 游戏电竞" "$REPORT_FILE" | grep "### 1\." | sed 's/### 1\. //'
        
        echo ""
        echo "📋 报告统计:"
        grep -E "资讯总数|Google News|本地数据源|平均相关性" "$REPORT_FILE"
        
        echo ""
        echo "🔗 查看完整报告:"
        echo "   cat $REPORT_FILE"
        echo ""
        echo "💡 增强版特点:"
        echo "   ✅ Google News API 集成 (API Key: app-ur6S2QXl17jGZrmqr4ssVy3r)"
        echo "   ✅ 智能降级机制 (API失败时自动切换)"
        echo "   ✅ 双数据源融合 (实时 + 本地备份)"
        echo "   ✅ 数据源标识 (🔍 Google News, 📋 本地数据)"
        echo "   ✅ 相关性评分排序"
        
    else
        echo "⚠️  警告: 报告文件未找到"
    fi
    
else
    echo "❌ 增强版日报生成失败"
    echo "🔧 可能的原因:"
    echo "   - Google News API 连接问题"
    echo "   - 网络连接问题"
    echo "   - 依赖文件缺失"
    exit 1
fi

# 记录完成时间
END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo ""
echo "⏰ 完成时间: $END_TIME"
echo "🎉 增强版日报生成完成!"

# 显示Google News API状态
echo ""
echo "📡 Google News API 状态:"
if [ -n "$GOOGLE_NEWS_API_KEY" ]; then
    echo "   ✅ API Key 已配置"
else
    echo "   ⚠️  API Key 未配置，使用模拟数据"
fi
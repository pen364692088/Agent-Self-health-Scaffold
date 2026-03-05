#!/bin/bash

# Awesome OpenClaw Skills Installer
# 从 awesome-openclaw-skills 列表中批量安装精选技能

set -e

echo "🚀 Awesome OpenClaw Skills Installer"
echo "====================================="

# 检查 clawhub 是否可用
if ! command -v clawhub &> /dev/null; then
    echo "❌ 错误: 未找到 clawhub CLI"
    echo "请先安装: npm install -g clawhub"
    exit 1
fi

# 定义要安装的精选技能列表
declare -A SELECTED_SKILLS=(
    # AI & LLMs
    ["cc-godmode"]="Self-orchestrating multi-agent development workflows"
    ["evolver"]="A self-evolution engine for AI agents"
    ["agent-council"]="Complete toolkit for creating autonomous AI agents"
    
    # Coding & Development
    ["coding-agent"]="Run Codex CLI, Claude Code, OpenCode, or Pi Coding Agent"
    ["cursor-agent"]="A comprehensive skill for using the Cursor CLI agent"
    ["debug-pro"]="Systematic debugging methodology"
    
    # Productivity & Tasks
    ["idea-coach"]="AI-powered idea/problem/challenge manager"
    ["essence-distiller"]="Find what actually matters in your content"
    
    # Search & Research
    ["get-tldr"]="Provide article summaries via get-tldr.com API"
    
    # Browser & Automation
    ["browse"]="Complete guide for creating and deploying browser automation"
    
    # Notes & PKM
    ["logseq"]="Provide commands for interacting with local Logseq instance"
    
    # Security
    ["identity-manager"]="Strictly manages user identity mappings"
)

# 计数器
TOTAL_SKILLS=${#SELECTED_SKILLS[@]}
INSTALLED=0
SKIPPED=0
FAILED=0

echo "📋 准备安装 $TOTAL_SKILLS 个精选技能..."
echo ""

# 创建安装日志
LOG_FILE="/tmp/awesome-skills-install-$(date +%Y%m%d-%H%M%S).log"
echo "📝 安装日志: $LOG_FILE"

function install_skill() {
    local skill_name="$1"
    local description="$2"
    
    echo -n "🔧 安装 $skill_name... "
    
    # 检查是否已安装
    if clawhub list | grep -q "$skill_name"; then
        echo "⚠️  已存在，跳过"
        ((SKIPPED++))
        echo "[$(date '+%H:%M:%S')] SKIPPED: $skill_name - $description" >> "$LOG_FILE"
        return 0
    fi
    
    # 尝试安装
    if clawhub install "$skill_name" >> "$LOG_FILE" 2>&1; then
        echo "✅ 成功"
        ((INSTALLED++))
        echo "[$(date '+%H:%M:%S')] INSTALLED: $skill_name - $description" >> "$LOG_FILE"
        return 0
    else
        # 检查是否因为可疑被阻止
        if grep -q "suspicious" "$LOG_FILE" 2>/dev/null; then
            echo "⚠️  被标记为可疑，跳过"
            ((SKIPPED++))
            echo "[$(date '+%H:%M:%S')] SKIPPED (suspicious): $skill_name - $description" >> "$LOG_FILE"
        else
            echo "❌ 失败"
            ((FAILED++))
            echo "[$(date '+%H:%M:%S')] FAILED: $skill_name - $description" >> "$LOG_FILE"
        fi
        return 1
    fi
}

# 显示技能列表
echo "📚 精选技能列表:"
echo "=================="
for skill in "${!SELECTED_SKILLS[@]}"; do
    echo "• $skill - ${SELECTED_SKILLS[$skill]}"
done
echo ""

# 询问用户确认
read -p "是否继续安装这些技能? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 用户取消安装"
    exit 0
fi

echo ""
echo "🚀 开始安装..."
echo "============="

# 安装每个技能
for skill in "${!SELECTED_SKILLS[@]}"; do
    install_skill "$skill" "${SELECTED_SKILLS[$skill]}"
    
    # 添加小延迟避免API限制
    sleep 1
done

# 显示安装结果
echo ""
echo "📊 安装结果统计:"
echo "================"
echo "✅ 成功安装: $INSTALLED"
echo "⚠️  跳过 (已存在/可疑): $SKIPPED"
echo "❌ 安装失败: $FAILED"
echo "📋 总计: $TOTAL_SKILLS"

if [ $INSTALLED -gt 0 ]; then
    echo ""
    echo "🎉 新安装的技能:"
    clawhub list | tail -n $INSTALLED
fi

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "❌ 失败的技能请查看日志: $LOG_FILE"
fi

echo ""
echo "💡 使用提示:"
echo "==========="
echo "• 查看所有已安装技能: clawhub list"
echo "• 更新技能: clawhub update <skill-name>"
echo "• 卸载技能: clawhub uninstall <skill-name>"
echo "• 查看安装日志: cat $LOG_FILE"

echo ""
echo "🎉 安装完成!"
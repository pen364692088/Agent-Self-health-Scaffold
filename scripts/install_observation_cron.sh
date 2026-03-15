#!/bin/bash
# 观察窗口 Cron 安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CRON_CONF="$SCRIPT_DIR/observation_cron.conf"

echo "=== Self-Health 观察窗口 Cron 安装 ==="
echo ""
echo "项目目录: $PROJECT_DIR"
echo ""

# 检查 cron 服务
if ! command -v crontab &> /dev/null; then
    echo "❌ crontab 未安装"
    echo "   请先安装: sudo apt install cron"
    exit 1
fi

# 显示当前 crontab
echo "[当前 crontab 内容]"
crontab -l 2>/dev/null || echo "(空)"
echo ""

# 检查是否已安装
if crontab -l 2>/dev/null | grep -q "observation_daily_check"; then
    echo "⚠️  观察窗口 cron 已存在"
    echo ""
    read -p "是否覆盖? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi
    # 移除旧的
    crontab -l 2>/dev/null | grep -v "observation_daily_check" | grep -v "observation_cron" | crontab - 2>/dev/null || true
fi

# 添加新的 cron 任务
echo ""
echo "[添加 cron 任务]"
echo "每日 06:00 运行观察窗口检查"
echo ""

# 读取现有 crontab 并添加新任务
(crontab -l 2>/dev/null || true; echo ""; echo "# Self-Health 观察窗口每日监控"; echo "0 6 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/observation_daily_check.py >> $PROJECT_DIR/artifacts/observation_window/daily_logs/cron.log 2>&1") | crontab -

# 验证
echo "[验证安装]"
crontab -l | grep -A2 "Self-Health" || echo "❌ 安装失败"
echo ""

echo "✅ 安装完成"
echo ""
echo "日志位置: $PROJECT_DIR/artifacts/observation_window/daily_logs/"
echo ""
echo "手动测试:"
echo "  cd $PROJECT_DIR"
echo "  python3 scripts/observation_daily_check.py"

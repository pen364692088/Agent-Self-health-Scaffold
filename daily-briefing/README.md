# Daily Briefing System

自动生成每日简报，涵盖经济、战争、政策、科技、AI、游戏六大领域。

## 文件结构

```
daily-briefing/
├── config.md           # 配置文件
├── smart-fetch.js      # 主程序 (智能抓取)
├── fetch-briefing.js   # 基础版本 (网络抓取)
├── package.json        # 项目配置
├── README.md           # 说明文档
└── reports/            # 生成的报告
    ├── 2026-02-23.json # JSON格式报告
    └── 2026-02-23.md   # Markdown格式报告
```

## 使用方法

### 生成今日报告
```bash
cd /home/moonlight/.openclaw/workspace/daily-briefing
node smart-fetch.js
```

### 查看报告
```bash
# 查看今日 Markdown 报告
cat reports/$(date +%Y-%m-%d).md

# 查看 JSON 数据
cat reports/$(date +%Y-%m-%d).json
```

## 功能特点

1. **六大领域覆盖**: 经济、军事、政策、科技、AI、游戏
2. **智能摘要**: 每个领域精选3条最重要资讯
3. **影响评级**: 🔴高 🟡中 🟢低 三级影响评估
4. **多格式输出**: JSON (结构化数据) + Markdown (阅读友好)
5. **时间戳记录**: 生成时间和数据源追踪

## 数据源

当前版本使用精选摘要数据，模拟实时新闻。后续版本将接入：
- Reuters API
- Google News RSS
- 专业财经数据源
- 军事新闻聚合器
- 政策法规数据库
- 科技媒体RSS
- AI行业资讯
- 游戏产业报告

## 定制化

可在 `smart-fetch.js` 中修改：
- 新闻源配置
- 影响评级逻辑
- 输出格式
- 语言设置

## 自动化

可配合 cron 定时任务实现每日自动生成：
```bash
# 每天早上8点生成报告
0 8 * * * cd /home/moonlight/.openclaw/workspace/daily-briefing && node smart-fetch.js
```

## 输出示例

报告包含：
- 📈 经济财经：股市、央行政策、经济数据
- ⚔️ 国际军事：冲突动态、地缘政治
- 🏛️ 政策法规：重要法案、监管动态
- 💻 前沿科技：新产品发布、技术突破
- 🤖 人工智能：模型更新、行业动态
- 🎮 游戏电竞：大作发布、电竞赛事

每条资讯包含：标题、摘要、影响级别、信息源。
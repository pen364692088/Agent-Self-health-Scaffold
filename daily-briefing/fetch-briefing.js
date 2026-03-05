#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');

// NewsAPI search terms for each category
const SEARCH_TERMS = {
  economics: ['stock market', 'inflation', 'Federal Reserve', 'economy', 'GDP'],
  warfare: ['war', 'conflict', 'military', 'Ukraine', 'Israel', 'Gaza', 'defense'],
  policy: ['government', 'policy', 'regulation', 'Congress', 'election', 'law'],
  technology: ['technology', 'innovation', 'startup', 'tech company', 'software'],
  ai: ['artificial intelligence', 'AI', 'machine learning', 'OpenAI', 'ChatGPT', 'LLM'],
  gaming: ['gaming', 'video games', 'esports', 'Nintendo', 'PlayStation', 'Xbox']
};

// Mock data for demo (replace with real API calls)
function generateMockNews(category) {
  const mockData = {
    economics: [
      { title: '美联储暗示可能暂停加息，股市应声上涨', source: '财经头条', importance: 'high' },
      { title: '原油价格波动加剧，OPEC+会议备受关注', source: '能源市场', importance: 'medium' },
      { title: '中国制造业PMI数据超预期，经济复苏迹象显现', source: '经济观察', importance: 'high' }
    ],
    warfare: [
      { title: '俄乌冲突持续，东部战线出现新的炮击事件', source: '战地快讯', importance: 'high' },
      { title: '中东局势紧张，多国呼吁停火谈判', source: '国际新闻', importance: 'medium' },
      { title: '北约军演在东欧地区展开，规模创历史新高', source: '军事观察', importance: 'medium' }
    ],
    policy: [
      { title: '国会通过新科技监管法案，针对大型科技公司', source: '政策快报', importance: 'high' },
      { title: '环保新规即将生效，企业面临合规挑战', source: '法规动态', importance: 'medium' },
      { title: '医保改革方案公布，覆盖范围将进一步扩大', source: '政策解读', importance: 'high' }
    ],
    technology: [
      { title: '苹果发布新一代芯片，性能提升显著', source: '科技前沿', importance: 'high' },
      { title: '量子计算突破：新型量子比特稳定性大幅提高', source: '科研动态', importance: 'medium' },
      { title: '5G网络覆盖率突破90%，6G研发正式启动', source: '通信技术', importance: 'medium' }
    ],
    ai: [
      { title: 'OpenAI发布GPT-5预览版，多项能力大幅提升', source: 'AI快讯', importance: 'high' },
      { title: '谷歌推出多模态AI模型，可同时处理文本、图像和音频', source: '科技新闻', importance: 'high' },
      { title: 'AI医疗应用获重大突破，诊断准确率超越人类医生', source: '医疗科技', importance: 'medium' }
    ],
    gaming: [
      { title: '索尼发布PS5 Pro，支持8K游戏输出', source: '游戏资讯', importance: 'high' },
      { title: '《黑神话：悟空》销量破千万，国产游戏走向世界', source: '游戏产业', importance: 'medium' },
      { title: '电竞赛事观看人数创新高，行业商业化加速', source: '电竞新闻', importance: 'medium' }
    ]
  };
  
  return mockData[category] || [];
}

function extractTopItems(text, category) {
  // For now, use mock data. In production, this would parse real news sources
  return generateMockNews(category);
}

async function fetchWithTimeout(url, timeout = 5000) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(url, { 
      signal: controller.signal,
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    clearTimeout(timeoutId);
    
    if (!response.ok) return null;
    return await response.text();
  } catch (error) {
    return null;
  }
}

async function generateDailyBriefing() {
  const today = new Date().toISOString().split('T')[0];
  const report = {
    date: today,
    generated_at: new Date().toISOString(),
    categories: {}
  };
  
  // Ensure reports directory exists
  await fs.mkdir('/home/moonlight/.openclaw/workspace/daily-briefing/reports', { recursive: true });
  
  console.log('Generating daily briefing...');
  
  for (const [category, sources] of Object.entries(SOURCES)) {
    console.log(`Fetching ${category}...`);
    const items = [];
    
    for (const source of sources) {
      const content = await fetchWithTimeout(source);
      if (content) {
        const extracted = extractTopItems(content, category);
        items.push(...extracted);
        if (items.length >= 3) break;
      }
    }
    
    report.categories[category] = items.slice(0, 3);
  }
  
  // Save report
  const reportPath = `/home/moonlight/.openclaw/workspace/daily-briefing/reports/${today}.json`;
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  
  // Generate markdown version
  const markdown = generateMarkdownReport(report);
  const markdownPath = `/home/moonlight/.openclaw/workspace/daily-briefing/reports/${today}.md`;
  await fs.writeFile(markdownPath, markdown);
  
  console.log(`Daily briefing saved to ${reportPath} and ${markdownPath}`);
  return report;
}

function generateMarkdownReport(report) {
  let md = `# 日报 - ${report.date}\n\n`;
  md += `生成时间: ${new Date(report.generated_at).toLocaleString('zh-CN')}\n\n`;
  
  const categoryNames = {
    economics: '📈 经济',
    warfare: '⚔️ 战争',
    policy: '🏛️ 政策',
    technology: '💻 科技',
    ai: '🤖 AI',
    gaming: '🎮 游戏'
  };
  
  for (const [category, items] of Object.entries(report.categories)) {
    md += `## ${categoryNames[category] || category}\n\n`;
    
    if (items.length === 0) {
      md += `- 暂无重要事件\n\n`;
      continue;
    }
    
    items.forEach((item, index) => {
      md += `${index + 1}. **${item.title}**\n`;
      if (item.source !== 'auto-extracted') {
        md += `   - 来源: ${item.source}\n`;
      }
      md += '\n';
    });
  }
  
  md += `---\n*本报告由 AI 自动生成，仅供参考*`;
  
  return md;
}

// Run if called directly
if (require.main === module) {
  generateDailyBriefing().catch(console.error);
}

module.exports = { generateDailyBriefing };
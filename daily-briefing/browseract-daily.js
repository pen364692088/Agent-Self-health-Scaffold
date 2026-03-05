#!/usr/bin/env node

const fs = require('fs').promises;
const { execFile } = require('child_process');
const { promisify } = require('util');
const execFileAsync = promisify(execFile);

const PY = '/usr/bin/python3';
const SKILL_SCRIPT = '/home/moonlight/.openclaw/workspace/skills/phheng-google-news-api/scripts/google_news_api.py';
const API_KEY = process.env.BROWSERACT_API_KEY || 'app-ur6S2QXl17jGZrmqr4ssVy3r';

const TOPICS = {
  economics: 'economy inflation federal reserve markets',
  warfare: 'ukraine russia israel gaza military conflict',
  policy: 'policy regulation congress eu law',
  technology: 'apple microsoft google chip technology',
  ai: 'openai gpt-5.3 gemini claude ai',
  gaming: 'gta 6 nintendo switch 2 esports gaming industry'
};

const FALLBACK = {
  economics: [
    { title: '美联储政策预期仍主导全球风险资产波动', source: 'Fallback', summary: '市场继续围绕降息路径交易，美元与美债收益率波动加大。' },
    { title: '主要经济体通胀回落但服务业粘性仍在', source: 'Fallback', summary: '核心服务价格仍偏强，限制了央行快速宽松空间。' },
    { title: '中国稳增长政策持续发力，内需修复成为关键', source: 'Fallback', summary: '投资与消费结构优化仍是后续观察重点。' }
  ],
  warfare: [
    { title: '俄乌前线持续拉锯，局地攻防强度不减', source: 'Fallback', summary: '战线总体僵持，远程打击与补给能力仍是决定因素。' },
    { title: '中东局势仍高敏感，停火谈判反复', source: 'Fallback', summary: '人道与安全议题叠加，区域外溢风险仍在。' },
    { title: '红海航运安全压力延续，物流成本承压', source: 'Fallback', summary: '航线绕行带来的时效与成本问题继续影响供应链。' }
  ],
  policy: [
    { title: '多国推进AI与平台监管细则落地', source: 'Fallback', summary: '重点从原则转向执行与合规细则。' },
    { title: '贸易与产业政策继续围绕关键技术重构', source: 'Fallback', summary: '供应链韧性与本地化政策并行推进。' },
    { title: '财政与公共支出议题成为政策博弈焦点', source: 'Fallback', summary: '预算与增长平衡成为短期核心变量。' }
  ],
  technology: [
    { title: 'AI PC与终端侧推理成为科技公司新品主线', source: 'Fallback', summary: '芯片、系统和应用联动升级加速。' },
    { title: '先进制程与封装竞争继续升温', source: 'Fallback', summary: '算力需求带动上游设备与材料景气。' },
    { title: '云厂商继续加码AI基础设施投资', source: 'Fallback', summary: '资本开支高位运行，商业化回报受关注。' }
  ],
  ai: [
    { title: '大模型竞争转向“能力+成本+安全”三维', source: 'Fallback', summary: '企业更关注可落地性与总拥有成本。' },
    { title: '多模态与Agent能力成为新一轮产品焦点', source: 'Fallback', summary: '从单轮问答向任务执行持续演进。' },
    { title: 'AI监管与版权争议推动行业规范化', source: 'Fallback', summary: '合规与审计能力正在成为平台标配。' }
  ],
  gaming: [
    { title: '3A新品周期与主机迭代预期提振板块情绪', source: 'Fallback', summary: '内容供给与硬件升级形成共振。' },
    { title: '电竞商业化继续深化，赛事IP价值提升', source: 'Fallback', summary: '赞助与转播结构优化带来收入质量改善。' },
    { title: '跨平台与订阅制仍是发行端核心策略', source: 'Fallback', summary: '用户增长与留存效率成为关键指标。' }
  ]
};

function parseBrowserActOutput(stdout) {
  const text = (stdout || '').trim();
  if (!text) return [];
  try {
    const obj = JSON.parse(text);
    if (Array.isArray(obj)) return obj;
    if (Array.isArray(obj.data)) return obj.data;
  } catch {}

  // if stdout contains extra logs + json
  const start = text.indexOf('[');
  const end = text.lastIndexOf(']');
  if (start >= 0 && end > start) {
    try {
      return JSON.parse(text.slice(start, end + 1));
    } catch {}
  }
  return [];
}

async function fetchTopic(topic, keyword) {
  try {
    const { stdout } = await execFileAsync(
      PY,
      [SKILL_SCRIPT, keyword, 'past 24 hours', '3'],
      {
        env: { ...process.env, BROWSERACT_API_KEY: API_KEY },
        timeout: 20000,
        maxBuffer: 1024 * 1024 * 4
      }
    );
    const rows = parseBrowserActOutput(stdout).slice(0, 3);
    if (!rows.length) throw new Error('empty results');
    return rows.map((r) => ({
      title: r.headline || r.title || 'Untitled',
      source: r.source || 'BrowserAct',
      summary: `发布时间: ${r.published_time || 'N/A'}；作者: ${r.author || 'N/A'}`,
      link: r.news_link || r.link || ''
    }));
  } catch (e) {
    return FALLBACK[topic];
  }
}

async function main() {
  const date = new Date().toISOString().slice(0, 10);
  const outDir = '/home/moonlight/.openclaw/workspace/daily-briefing/reports';
  await fs.mkdir(outDir, { recursive: true });

  const categories = {};
  for (const [topic, q] of Object.entries(TOPICS)) {
    categories[topic] = await fetchTopic(topic, q);
  }

  const report = { date, source: 'browseract-google-news-api', categories };
  const md = renderMd(report);

  await fs.writeFile(`${outDir}/${date}-browseract.json`, JSON.stringify(report, null, 2));
  await fs.writeFile(`${outDir}/${date}-browseract.md`, md);
  console.log(`${outDir}/${date}-browseract.md`);
}

function renderMd(report) {
  const names = {
    economics: '📈 经济', warfare: '⚔️ 战争', policy: '🏛️ 政策', technology: '💻 科技', ai: '🤖 AI', gaming: '🎮 游戏'
  };
  let s = `# 日报（BrowserAct版）- ${report.date}\n\n来源：${report.source}\n\n`;
  for (const [k, arr] of Object.entries(report.categories)) {
    s += `## ${names[k] || k}\n\n`;
    arr.slice(0, 3).forEach((it, i) => {
      s += `${i + 1}. **${it.title}**\n`;
      s += `   - 来源：${it.source}\n`;
      s += `   - 摘要：${it.summary}\n`;
      if (it.link) s += `   - 链接：${it.link}\n`;
      s += `\n`;
    });
  }
  return s;
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});

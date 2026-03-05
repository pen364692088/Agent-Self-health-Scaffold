#!/usr/bin/env node
const fs = require('fs').promises;

const TOPICS = {
  economics: 'economy OR inflation OR "federal reserve" OR markets when:1d',
  warfare: 'ukraine OR gaza OR israel OR military conflict when:1d',
  policy: 'government policy OR regulation OR congress OR eu law when:1d',
  technology: 'apple OR microsoft OR google OR semiconductor OR technology when:1d',
  ai: 'OpenAI OR GPT-5.3 OR Gemini OR Claude OR AI model when:1d',
  gaming: 'gaming OR "GTA 6" OR "Switch 2" OR esports when:1d'
};

const NAMES = {
  economics: '📈 经济', warfare: '⚔️ 战争', policy: '🏛️ 政策',
  technology: '💻 科技', ai: '🤖 AI', gaming: '🎮 游戏'
};

const SOURCE_ALLOW = [
  'Reuters','BBC','Associated Press','AP News','Financial Times','WSJ','The Wall Street Journal',
  'Bloomberg','CNBC','The Verge','TechCrunch','Ars Technica','Wired','Nikkei','Politico',
  'Al Jazeera','The Guardian','Axios','MIT Technology Review','VentureBeat','Engadget','IGN','Polygon'
];

const CATEGORY_HINTS = {
  economics: ['economy','inflation','federal reserve','market','stocks','gdp','cpi','央行','经济','通胀'],
  warfare: ['war','military','ukraine','gaza','israel','nato','missile','conflict','战','军事','冲突'],
  policy: ['policy','regulation','law','congress','parliament','eu','government','法案','政策','监管'],
  technology: ['apple','microsoft','google','chip','semiconductor','tesla','spacex','technology','科技','芯片'],
  ai: ['openai','gpt','gemini','claude','llm','ai','artificial intelligence','智能体','大模型'],
  gaming: ['game','gaming','esports','nintendo','playstation','xbox','gta','switch','游戏','电竞']
};

function stripCdata(s=''){ return s.replace('<![CDATA[','').replace(']]>','').trim(); }

async function fetchRss(query) {
  const url = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=en-US&gl=US&ceid=US:en`;
  const res = await fetch(url, { headers: { 'user-agent': 'Mozilla/5.0' } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

function parseItems(xml) {
  const items = [];
  const chunks = xml.split('<item>').slice(1);
  for (const c of chunks) {
    const block = c.split('</item>')[0] || '';
    const titleFull = stripCdata((block.match(/<title>([\s\S]*?)<\/title>/)||[])[1]||'');
    const link = ((block.match(/<link>([\s\S]*?)<\/link>/)||[])[1]||'').trim();
    const pubDate = ((block.match(/<pubDate>([\s\S]*?)<\/pubDate>/)||[])[1]||'').trim();
    const descRaw = stripCdata((block.match(/<description>([\s\S]*?)<\/description>/)||[])[1]||'');
    const description = descRaw.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();
    if (!titleFull || !link) continue;
    const parts = titleFull.split(' - ');
    const source = parts.length > 1 ? parts[parts.length - 1].trim() : 'Unknown';
    const title = parts.length > 1 ? parts.slice(0, -1).join(' - ').trim() : titleFull;
    items.push({ title, source, link, pubDate, description });
  }
  return items;
}

function sourceAllowed(source='') {
  return SOURCE_ALLOW.some(s => source.toLowerCase().includes(s.toLowerCase()));
}

function scoreForCategory(item, cat) {
  const t = `${item.title} ${item.source}`.toLowerCase();
  return CATEGORY_HINTS[cat].reduce((n,k)=> n + (t.includes(k.toLowerCase()) ? 1 : 0), 0);
}

function summarize(item, cat) {
  const d = item.pubDate ? new Date(item.pubDate).toLocaleString('zh-CN') : 'N/A';
  const t = item.title;
  const zh = /[\u4e00-\u9fa5]/.test(t);
  const core = zh
    ? `核心信息：${t}`
    : `核心信息：该报道围绕“${t.slice(0, 72)}”展开，重点在于最新进展与市场/政策影响`;
  return `${core}。（${item.source}，${d}）`;
}

async function main(){
  const date = new Date().toISOString().slice(0,10);
  const pool = [];

  for (const q of Object.values(TOPICS)) {
    try {
      const xml = await fetchRss(q);
      pool.push(...parseItems(xml));
    } catch {}
  }

  // whitelist + dedup by title
  const dedupMap = new Map();
  for (const it of pool) {
    if (!sourceAllowed(it.source)) continue;
    const key = it.title.toLowerCase();
    if (!dedupMap.has(key)) dedupMap.set(key, it);
  }
  const dedup = Array.from(dedupMap.values());

  const used = new Set();
  const categories = {};
  for (const cat of Object.keys(TOPICS)) {
    const ranked = dedup
      .map(it => ({...it, sc: scoreForCategory(it, cat)}))
      .filter(it => it.sc > 0 && !used.has(it.title.toLowerCase()))
      .sort((a,b)=> b.sc - a.sc || new Date(b.pubDate) - new Date(a.pubDate));

    categories[cat] = ranked.slice(0,3).map(it => {
      used.add(it.title.toLowerCase());
      return {
        title: it.title,
        source: it.source,
        pubDate: it.pubDate,
        link: it.link,
        summary: summarize(it, cat)
      };
    });
  }

  const report = { date, source:'google-news-rss-live-v2', categories, totalPool: pool.length, totalClean: dedup.length };
  const text = render(report);

  const dir = '/home/moonlight/.openclaw/workspace/daily-briefing/reports';
  await fs.mkdir(dir,{recursive:true});
  await fs.writeFile(`${dir}/${date}-realtime-rss-v2.txt`, text);
  await fs.writeFile(`${dir}/${date}-realtime-rss-v2.json`, JSON.stringify(report,null,2));
  console.log(`${dir}/${date}-realtime-rss-v2.txt`);
}

function render(report){
  let out = `日报（纯实时抓取 v2）- ${report.date}\n`;
  out += `来源：${report.source}｜原始抓取 ${report.totalPool} 条，清洗后 ${report.totalClean} 条\n\n`;
  for (const [cat, arr] of Object.entries(report.categories)) {
    out += `${NAMES[cat]}\n`;
    if (!arr.length) {
      out += `1. 暂无高质量可用新闻（已按白名单过滤）\n\n`;
      continue;
    }
    arr.forEach((it,i)=>{
      out += `${i+1}. ${it.title}\n`;
      out += `- 来源：${it.source}\n`;
      out += `- 摘要：${it.summary}\n`;
      out += `- 链接：${it.link}\n`;
    });
    out += '\n';
  }
  return out;
}

main().catch(e=>{console.error(e.message);process.exit(1)});
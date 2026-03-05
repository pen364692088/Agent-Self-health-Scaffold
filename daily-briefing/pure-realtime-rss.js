#!/usr/bin/env node
const fs = require('fs').promises;

const TOPICS = {
  economics: 'economy OR inflation OR "federal reserve" when:1d',
  warfare: 'ukraine OR gaza OR israel OR military conflict when:1d',
  policy: 'government policy OR regulation OR congress OR eu law when:1d',
  technology: 'technology OR chip OR apple OR microsoft OR google when:1d',
  ai: 'OpenAI OR GPT-5.3 OR Gemini OR Claude AI when:1d',
  gaming: 'gaming OR "GTA 6" OR "Switch 2" OR esports when:1d'
};

const NAMES = {
  economics: '📈 经济',
  warfare: '⚔️ 战争',
  policy: '🏛️ 政策',
  technology: '💻 科技',
  ai: '🤖 AI',
  gaming: '🎮 游戏'
};

async function fetchRss(query) {
  const url = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans`;
  const res = await fetch(url, { headers: { 'user-agent': 'Mozilla/5.0' } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

function stripCdata(s=''){ return s.replace('<![CDATA[','').replace(']]>','').trim(); }

function parseItems(xml) {
  const items = [];
  const chunks = xml.split('<item>').slice(1);
  for (const c of chunks) {
    const block = c.split('</item>')[0] || '';
    const title = stripCdata((block.match(/<title>([\s\S]*?)<\/title>/)||[])[1]||'');
    const link = ((block.match(/<link>([\s\S]*?)<\/link>/)||[])[1]||'').trim();
    const pubDate = ((block.match(/<pubDate>([\s\S]*?)<\/pubDate>/)||[])[1]||'').trim();
    if (title && link) items.push({ title, link, pubDate });
  }
  return items;
}

function render(report){
  let out = `日报（纯实时抓取）- ${report.date}\n\n`;
  for (const [k,v] of Object.entries(report.categories)) {
    out += `${NAMES[k]}\n`;
    v.forEach((it,i)=>{
      out += `${i+1}. ${it.title}\n- 时间：${it.pubDate || 'N/A'}\n- 链接：${it.link}\n`;
    });
    out += '\n';
  }
  return out;
}

async function main(){
  const date = new Date().toISOString().slice(0,10);
  const categories = {};
  for (const [k,q] of Object.entries(TOPICS)) {
    try {
      const xml = await fetchRss(q);
      categories[k] = parseItems(xml).slice(0,3);
    } catch {
      categories[k] = [];
    }
  }
  const report = { date, source:'google-news-rss-live', categories };
  const md = render(report);
  const dir = '/home/moonlight/.openclaw/workspace/daily-briefing/reports';
  await fs.mkdir(dir,{recursive:true});
  await fs.writeFile(`${dir}/${date}-realtime-rss.txt`, md);
  await fs.writeFile(`${dir}/${date}-realtime-rss.json`, JSON.stringify(report,null,2));
  console.log(`${dir}/${date}-realtime-rss.txt`);
}

main().catch(e=>{console.error(e.message);process.exit(1)});
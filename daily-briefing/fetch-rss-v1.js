#!/usr/bin/env node
const { execSync } = require('child_process');
const fs = require('fs');

const MAX_AGE_HOURS = Number(process.env.BRIEFING_MAX_AGE_HOURS || 48);
const NEWS_TIMEOUT_MS = Number(process.env.BRIEFING_FETCH_TIMEOUT_MS || 15000);

function stripTags(s = '') {
  return s
    .replace(/<!\[CDATA\[(.*?)\]\]>/g, '$1')
    .replace(/<[^>]*>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .trim();
}

function normalizeTitle(s = '') {
  return s
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/[“”"'`]/g, '')
    .trim();
}

function stripSourceSuffix(title, source) {
  if (!title || !source) return title;
  const escaped = source.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`\\s[-–—]\\s${escaped}$`, 'i');
  return title.replace(re, '').trim();
}

function parseItems(xml) {
  const items = [];
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let m;
  while ((m = itemRegex.exec(xml)) !== null) {
    const block = m[1] || '';
    const title = stripTags((block.match(/<title>([\s\S]*?)<\/title>/i) || [])[1] || '');
    const pubRaw = stripTags((block.match(/<pubDate>([\s\S]*?)<\/pubDate>/i) || [])[1] || '');
    const source = stripTags((block.match(/<source[^>]*>([\s\S]*?)<\/source>/i) || [])[1] || '');
    const cleanTitle = stripSourceSuffix(title, source);

    if (!cleanTitle || /^google news$/i.test(cleanTitle)) continue;
    const pubMs = Date.parse(pubRaw);
    items.push({ title: cleanTitle, source: source || null, pubRaw: pubRaw || null, pubMs: Number.isFinite(pubMs) ? pubMs : null });
  }
  return items;
}

function withinAge(item, nowMs, maxAgeHours) {
  if (!item.pubMs) return true; // keep undated items as fallback
  const ageH = (nowMs - item.pubMs) / 3600000;
  return ageH >= -6 && ageH <= maxAgeHours;
}

function fetchNews(query, fallbackQuery = null) {
  const nowMs = Date.now();
  const tried = [];

  for (const q of [query, fallbackQuery].filter(Boolean)) {
    tried.push(q);
    try {
      const url = `https://news.google.com/rss/search?q=${encodeURIComponent(q)}&hl=en-US&gl=US&ceid=US:en`;
      const xml = execSync(`curl -s -L --max-time ${Math.ceil(NEWS_TIMEOUT_MS / 1000)} "${url}"`, {
        encoding: 'utf8',
        timeout: NEWS_TIMEOUT_MS,
        maxBuffer: 1024 * 1024 * 8
      });

      const seen = new Set();
      const fresh = [];
      for (const item of parseItems(xml)) {
        if (!withinAge(item, nowMs, MAX_AGE_HOURS)) continue;
        const key = normalizeTitle(item.title);
        if (!key || seen.has(key)) continue;
        seen.add(key);
        fresh.push(item);
        if (fresh.length >= 6) break;
      }

      if (fresh.length >= 3) return fresh.slice(0, 3);
      if (fresh.length > 0 && !fallbackQuery) return fresh.slice(0, 3);
    } catch (_) {
      // try fallback query
    }
  }

  return [];
}

function fetchBtc() {
  try {
    const stdout = execSync('curl -s --max-time 10 "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true&sparkline=false"', { encoding: 'utf8' });
    const data = JSON.parse(stdout);
    const price = Number(data.market_data?.current_price?.usd || 0);
    const change24h = Number(data.market_data?.price_change_percentage_24h_in_currency?.usd || 0);
    if (!price) throw new Error('no price');
    const trend = change24h >= 0 ? '上涨' : '回调';
    const support = Math.floor(price * 0.78);
    return `• 比特币现价≈$${Math.round(price)}，24h ${change24h >= 0 ? '+' : ''}${change24h.toFixed(2)}%。 • 影响：短期技术面${trend}，支撑位关注$${support}。\n• 今日趋势判断：${trend}。\n• 风险提示：波动性高，严控仓位，做好止损。`;
  } catch (_) {
    return '• 比特币价格获取失败。';
  }
}

function renderSection(title, items) {
  let out = `${title}\n`;
  if (!items.length) {
    out += '• 暂无足够新鲜数据（已过滤过旧新闻）\n';
    return out;
  }
  for (const it of items.slice(0, 3)) {
    out += `• ${it.title}${it.source ? ` - ${it.source}` : ''}\n`;
  }
  return out;
}

async function main() {
  const today = new Date().toISOString().slice(0, 10);

  const categories = {
    '📈 经济': ['stock market earnings inflation fed', 'economy markets today'],
    '⚔️ 战争': ['ukraine russia war latest', 'middle east conflict latest'],
    '🏛️ 政策': ['government policy congress regulation latest', 'public policy latest'],
    '💻 科技': ['technology news smartphones semiconductor cloud latest', 'tech industry latest'],
    '🤖 AI': ['artificial intelligence openai google anthropic latest', 'AI model regulation latest'],
    '🎮 游戏': ['video game release esports latest', 'gaming industry latest']
  };

  let report = `【每日要闻 ${today}】\n\n`;

  for (const [title, [primary, fallback]] of Object.entries(categories)) {
    const news = fetchNews(primary, fallback);
    report += renderSection(title, news);
  }

  report += '₿ BTC\n' + fetchBtc() + '\n';
  report += '\n*仅供参考，不构成投资建议。*';

  console.log(report);

  const dir = '/home/moonlight/.openclaw/workspace/daily-briefing/reports';
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(`${dir}/${today}-curl-rss.txt`, report);
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});

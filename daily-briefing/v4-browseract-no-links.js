#!/usr/bin/env node
const fs = require('fs').promises;
const { execFile } = require('child_process');
const { promisify } = require('util');
const execFileAsync = promisify(execFile);

const PY = '/usr/bin/python3';
const SKILL_SCRIPT = '/home/moonlight/.openclaw/workspace/skills/phheng-google-news-api/scripts/google_news_api.py';
const API_KEY = process.env.BROWSERACT_API_KEY || 'app-ur6S2QXl17jGZrmqr4ssVy3r';

const TOPICS = {
  economics: 'economy inflation federal reserve market',
  warfare: 'ukraine russia gaza israel military conflict',
  policy: 'policy regulation congress eu law government',
  technology: 'apple microsoft google semiconductor technology',
  ai: 'openai gpt-5.3 gemini claude ai model',
  gaming: 'gta 6 switch 2 xbox playstation esports'
};

const NAMES = {
  economics: '📈 经济', warfare: '⚔️ 战争', policy: '🏛️ 政策', technology: '💻 科技', ai: '🤖 AI', gaming: '🎮 游戏'
};

function parseRows(stdout) {
  const text = (stdout || '').trim();
  if (!text) return [];
  try {
    const arr = JSON.parse(text);
    return Array.isArray(arr) ? arr : [];
  } catch {}
  const s = text.indexOf('['), e = text.lastIndexOf(']');
  if (s >= 0 && e > s) {
    try { return JSON.parse(text.slice(s, e + 1)); } catch {}
  }
  return [];
}

function summarizeHeadline(h) {
  const t = (h || '').trim();
  if (!t) return '暂无可提炼信息。';
  const zh = /[\u4e00-\u9fa5]/.test(t);
  if (zh) return `要点：${t}。影响：短期内将影响相关领域预期与决策。`;
  return `要点：${t}。影响：This development may materially affect near-term expectations in its sector.`;
}

async function fetchTopic(topic, q) {
  try {
    const { stdout } = await execFileAsync(
      PY,
      [SKILL_SCRIPT, q, 'past 24 hours', '6'],
      { env: { ...process.env, BROWSERACT_API_KEY: API_KEY }, timeout: 45000, maxBuffer: 1024 * 1024 * 4 }
    );
    const rows = parseRows(stdout)
      .filter(r => r && (r.headline || r.title))
      .slice(0, 3)
      .map(r => ({
        title: r.headline || r.title,
        source: r.source || 'Unknown',
        published: r.published_time || 'N/A',
        summary: summarizeHeadline(r.headline || r.title)
      }));
    return rows;
  } catch {
    return [];
  }
}

function render(report) {
  let s = `日报（v4：BrowserAct增强，无链接版）- ${report.date}\n\n`;
  for (const [k, arr] of Object.entries(report.categories)) {
    s += `${NAMES[k]}\n`;
    if (!arr.length) {
      s += `1. 暂无可用实时结果（该栏稍后补发）\n\n`;
      continue;
    }
    arr.forEach((it, i) => {
      s += `${i + 1}. ${it.title}\n`;
      s += `- 来源：${it.source}\n`;
      s += `- 时间：${it.published}\n`;
      s += `- 摘要：${it.summary}\n`;
    });
    s += '\n';
  }
  return s;
}

async function loadV3Fallback(date) {
  try {
    const p = `/home/moonlight/.openclaw/workspace/daily-briefing/reports/${date}-realtime-rss-v3.json`;
    const raw = await fs.readFile(p, 'utf-8');
    return JSON.parse(raw).categories || {};
  } catch { return {}; }
}

async function main() {
  const date = new Date().toISOString().slice(0, 10);
  const v3 = await loadV3Fallback(date);
  const categories = {};
  for (const [k, q] of Object.entries(TOPICS)) {
    const live = await fetchTopic(k, q);
    if (live.length) {
      categories[k] = live;
    } else {
      const fb = (v3[k] || []).slice(0, 3).map(it => ({
        title: it.title,
        source: it.source || 'RSS',
        published: it.pubDate || 'N/A',
        summary: it.summary || summarizeHeadline(it.title)
      }));
      categories[k] = fb;
    }
  }
  const report = { date, source: 'browseract-v4-with-v3-fallback', categories };
  const txt = render(report);
  const dir = '/home/moonlight/.openclaw/workspace/daily-briefing/reports';
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(`${dir}/${date}-v4-no-links.txt`, txt);
  await fs.writeFile(`${dir}/${date}-v4-no-links.json`, JSON.stringify(report, null, 2));
  console.log(txt);
}

main().catch(e => { console.error(e.message); process.exit(1); });
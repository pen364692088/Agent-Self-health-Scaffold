#!/usr/bin/env node

/**
 * memory-lancedb-seed - 直接写入测试数据到 LanceDB
 * 
 * Usage:
 *   node memory-lancedb-seed.mjs --seed
 *   node memory-lancedb-seed.mjs --status
 */

import * as lancedb from '@lancedb/lancedb';
import { OpenAI } from 'openai';
import { randomUUID } from 'crypto';
import { existsSync, mkdirSync } from 'fs';
import { resolve, homedir } from 'path';

const LANCEDB_PATH = resolve(homedir(), '.openclaw/memory/lancedb');
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://192.168.79.1:11434';

// Embedding 客户端 (Ollama 兼容 OpenAI API)
const embeddingClient = new OpenAI({
  apiKey: 'ollama-local',
  baseURL: OLLAMA_BASE_URL + '/v1',
});

async function getEmbedding(text) {
  const response = await embeddingClient.embeddings.create({
    model: 'mxbai-embed-large',
    input: text,
    dimensions: 1024,
  });
  return response.data[0].embedding;
}

async function seedDatabase() {
  console.log('=== Seeding LanceDB ===');
  console.log('Path:', LANCEDB_PATH);
  
  // 确保目录存在
  const dbDir = resolve(LANCEDB_PATH, '..');
  if (!existsSync(dbDir)) {
    mkdirSync(dbDir, { recursive: true });
  }
  
  // 连接数据库
  const db = await lancedb.connect(LANCEDB_PATH);
  console.log('Connected to LanceDB');
  
  // 测试数据
  const testEntries = [
    {
      text: 'Gate 1.7 test: verify memory-lancedb population and retrieval. This is a test entry for validation.',
      importance: 0.9,
      category: 'test',
    },
    {
      text: 'Execution Policy enforcement: verify-and-close must be called before task completion. Use safe-write for sensitive paths.',
      importance: 0.8,
      category: 'policy',
    },
    {
      text: 'Session Continuity: session-start-recovery must be called at the start of every new session to restore state.',
      importance: 0.85,
      category: 'continuity',
    },
  ];
  
  // 生成 embeddings 并创建记录
  const entries = [];
  for (const entry of testEntries) {
    console.log(`Getting embedding for: ${entry.text.substring(0, 50)}...`);
    const vector = await getEmbedding(entry.text);
    
    entries.push({
      id: randomUUID(),
      text: entry.text,
      vector: vector,
      importance: entry.importance,
      category: entry.category,
      createdAt: Date.now(),
    });
  }
  
  // 创建表
  const tableName = 'memories';
  const table = await db.createTable(tableName, entries, { mode: 'overwrite' });
  console.log(`✅ Seeded ${entries.length} entries to LanceDB table '${tableName}'`);
  
  // 验证
  const count = await table.countRows();
  console.log(`Total rows in table: ${count}`);
  
  return 0;
}

async function checkStatus() {
  console.log('=== LanceDB Status ===');
  console.log('Path:', LANCEDB_PATH);
  console.log('Exists:', existsSync(LANCEDB_PATH));
  
  try {
    const db = await lancedb.connect(LANCEDB_PATH);
    const tables = await db.tableNames();
    console.log('Tables:', tables);
    
    if (tables.includes('memories')) {
      const table = await db.openTable('memories');
      const count = await table.countRows();
      console.log('Memory count:', count);
    }
  } catch (e) {
    console.log('Error:', e.message);
  }
  
  return 0;
}

async function recallData(query) {
  console.log(`=== Recall: '${query}' ===`);
  
  try {
    const db = await lancedb.connect(LANCEDB_PATH);
    
    const tables = await db.tableNames();
    if (!tables.includes('memories')) {
      console.log("No 'memories' table found");
      return 1;
    }
    
    const table = await db.openTable('memories');
    
    // 获取 query embedding
    const vector = await getEmbedding(query);
    
    // 搜索
    const results = await table.vectorSearch(vector).limit(5).toArray();
    
    if (results.length === 0) {
      console.log('No results found');
    } else {
      console.log(`Found ${results.length} results:`);
      for (const row of results) {
        console.log(`\n- Distance: ${row._distance || 'N/A'}`);
        console.log(`  Text: ${row.text ? row.text.substring(0, 100) : 'N/A'}...`);
        console.log(`  Category: ${row.category || 'N/A'}`);
      }
    }
    
    return 0;
  } catch (e) {
    console.log('Error:', e.message);
    return 1;
  }
}

// 主入口
const args = process.argv.slice(2);

if (args.includes('--seed')) {
  seedDatabase().then(code => process.exit(code));
} else if (args.includes('--status')) {
  checkStatus().then(code => process.exit(code));
} else if (args.includes('--recall')) {
  const idx = args.indexOf('--recall');
  const query = args[idx + 1];
  recallData(query).then(code => process.exit(code));
} else {
  console.log('Usage:');
  console.log('  node memory-lancedb-seed.mjs --seed');
  console.log('  node memory-lancedb-seed.mjs --status');
  console.log('  node memory-lancedb-seed.mjs --recall "query"');
  process.exit(0);
}

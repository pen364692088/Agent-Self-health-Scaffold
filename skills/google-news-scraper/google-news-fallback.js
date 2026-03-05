#!/usr/bin/env node

// Google News Scraper with Fallback Methods
// Uses multiple sources when API is unavailable

const https = require('https');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const API_KEY = "app-ur6S2QXl17jGZrmqr4ssVy3r";
const BASE_URL = "https://newsapi.org/v2";

// Fallback RSS sources
const RSS_SOURCES = {
    technology: [
        "https://feeds.feedburner.com/TechCrunch",
        "https://www.wired.com/feed/rss",
        "https://feeds.macrumors.com/",
        "https://feeds.arstechnica.com/arstechnica/index"
    ],
    business: [
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://feeds.reuters.com/news/wealth",
        "https://feeds.finance.yahoo.com/rss/2.0/headline",
        "https://feeds.feedburner.com/Forbes"
    ],
    science: [
        "https://www.scientificamerican.com/feed/",
        "https://www.nature.com/nature/articles?type=news&format=rss",
        "https://feeds.feedburner.com/sciencealert-latest",
        "https://rss.sciam.com/ScientificAmerican-Global/News"
    ],
    ai: [
        "https://venturebeat.com/ai/feed/",
        "https://artificialintelligence-news.com/feed/",
        "https://techcrunch.com/category/artificial-intelligence/feed/"
    ]
};

// Colors for console output
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
};

function colorLog(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

// Make HTTP request
function makeRequest(url) {
    return new Promise((resolve, reject) => {
        const request = https.get(url, (response) => {
            let data = '';
            
            response.on('data', (chunk) => {
                data += chunk;
            });
            
            response.on('end', () => {
                if (response.statusCode === 200) {
                    try {
                        const jsonData = JSON.parse(data);
                        resolve(jsonData);
                    } catch (error) {
                        resolve(data); // Return raw data if not JSON
                    }
                } else {
                    reject(new Error(`HTTP ${response.statusCode}: ${data}`));
                }
            });
        });
        
        request.on('error', (error) => {
            reject(error);
        });
        
        request.setTimeout(10000, () => {
            request.destroy();
            reject(new Error('Request timeout'));
        });
    });
}

// Try Google News API
async function tryGoogleAPI(endpoint, params = {}) {
    try {
        colorLog('🔍 Trying Google News API...', 'blue');
        
        const queryString = new URLSearchParams({
            apiKey: API_KEY,
            pageSize: '10',
            ...params
        }).toString();
        
        const url = `${BASE_URL}/${endpoint}?${queryString}`;
        const response = await makeRequest(url);
        
        if (response.status === 'error') {
            throw new Error(response.message);
        }
        
        colorLog('✅ Google News API success!', 'green');
        return response;
        
    } catch (error) {
        colorLog(`❌ Google News API failed: ${error.message}`, 'red');
        return null;
    }
}

// Parse RSS feed
function parseRSS(xmlData) {
    try {
        const items = [];
        const itemRegex = /<item>(.*?)<\/item>/gs;
        const titleRegex = /<title><!\[CDATA\[(.*?)\]\]><\/title>/gs;
        const linkRegex = /<link>(.*?)<\/link>/gs;
        const descRegex = /<description><!\[CDATA\[(.*?)\]\]><\/description>/gs;
        const pubDateRegex = /<pubDate>(.*?)<\/pubDate>/gs;
        
        let match;
        while ((match = itemRegex.exec(xmlData)) !== null) {
            const itemContent = match[1];
            
            const titleMatch = titleRegex.exec(itemContent);
            const linkMatch = linkRegex.exec(itemContent);
            const descMatch = descRegex.exec(itemContent);
            const pubDateMatch = pubDateRegex.exec(itemContent);
            
            if (titleMatch && linkMatch) {
                items.push({
                    title: titleMatch[1],
                    url: linkMatch[1],
                    description: descMatch ? descMatch[1].replace(/<[^>]*>/g, '').substring(0, 200) + '...' : 'No description',
                    publishedAt: pubDateMatch ? pubDateMatch[1] : new Date().toISOString(),
                    source: { name: 'RSS Feed' }
                });
            }
        }
        
        return items;
    } catch (error) {
        colorLog(`RSS parsing error: ${error.message}`, 'red');
        return [];
    }
}

// Fetch from RSS feeds
async function fetchFromRSS(category, limit = 5) {
    const sources = RSS_SOURCES[category] || RSS_SOURCES.technology;
    const allArticles = [];
    
    colorLog(`📡 Fetching from RSS sources for ${category}...`, 'yellow');
    
    for (const source of sources.slice(0, 3)) { // Limit to 3 sources
        try {
            const data = await makeRequest(source);
            const articles = parseRSS(data);
            allArticles.push(...articles);
            
            // Add delay to be respectful
            await new Promise(resolve => setTimeout(resolve, 1000));
            
        } catch (error) {
            colorLog(`Failed to fetch ${source}: ${error.message}`, 'red');
        }
    }
    
    // Return latest articles
    return allArticles
        .sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt))
        .slice(0, limit);
}

// Generate mock news as last resort
function generateMockNews(category, limit = 5) {
    colorLog(`🎭 Generating mock news for ${category}...`, 'magenta');
    
    const mockTemplates = {
        technology: [
            { title: "AI Breakthrough: New Model Achieves Human-Level Performance", description: "Researchers announce a breakthrough in artificial intelligence..." },
            { title: "Apple Reveals Next-Generation Silicon Chips", description: "Apple's latest silicon promises significant performance improvements..." },
            { title: "Quantum Computing Reaches New Milestone", description: "Scientists demonstrate quantum supremacy in practical applications..." },
            { title: "Cybersecurity Alert: New Vulnerability Discovered", description: "Security researchers identify critical vulnerability in popular software..." },
            { title: "SpaceX Launches Record-Breaking Satellite Constellation", description: "Elon Musk's company deploys largest satellite network ever..." }
        ],
        business: [
            { title: "Stock Markets Rally on Positive Economic Data", description: "Global markets surged today as economic indicators exceeded expectations..." },
            { title: "Federal Reserve Signals Potential Rate Changes", description: "Central bank officials hint at upcoming monetary policy adjustments..." },
            { title: "Tech Giants Report Strong Quarterly Earnings", description: "Major technology companies beat analyst expectations with robust growth..." },
            { title: "Cryptocurrency Market Shows Remarkable Recovery", description: "Digital assets experience significant price appreciation..." },
            { title: "Global Supply Chain Improves, Inflation Eases", description: "Manufacturing and logistics sectors show signs of normalization..." }
        ],
        science: [
            { title: "Scientists Discover New Species in Deep Ocean", description: "Marine biologists identify previously unknown creatures in abyssal zones..." },
            { title: "Climate Research Reveals Urgent Action Needed", description: "New study underscores the critical importance of immediate climate action..." },
            { title: "Medical Breakthrough: Promising Cancer Treatment", description: "Clinical trials show remarkable results for innovative therapy..." },
            { title: "Space Telescope Detects Distant Galaxy Formation", description: "Astronomers observe early universe galaxy formation in unprecedented detail..." },
            { title: "Renewable Energy Achieves Cost Parity", description: "Solar and wind power now competitive with fossil fuels..." }
        ],
        ai: [
            { title: "OpenAI Announces Next-Generation Language Model", description: "Latest AI model demonstrates unprecedented capabilities in reasoning and creativity..." },
            { title: "Google DeepMind Achieves AGI Milestone", description: "Research team claims significant progress toward artificial general intelligence..." },
            { title: "AI Ethics Framework Adopted Globally", description: "International consensus reached on responsible AI development guidelines..." },
            { title: "Machine Learning Revolutionizes Drug Discovery", description: "AI-powered processes accelerate pharmaceutical research dramatically..." },
            { title: "Autonomous Systems Pass Critical Safety Tests", description: "Self-driving technology achieves major safety certification milestone..." }
        ]
    };
    
    const templates = mockTemplates[category] || mockTemplates.technology;
    const articles = [];
    
    for (let i = 0; i < Math.min(limit, templates.length); i++) {
        const template = templates[i];
        articles.push({
            title: template.title,
            description: template.description,
            url: `https://example.com/news/${Date.now()}-${i}`,
            publishedAt: new Date(Date.now() - i * 3600000).toISOString(),
            source: { name: 'Generated News' }
        });
    }
    
    return articles;
}

// Format output
function formatOutput(articles, format = 'default') {
    if (format === 'json') {
        return JSON.stringify({ articles }, null, 2);
    }
    
    if (format === 'csv') {
        const header = 'Source,Title,Description,Published,URL\n';
        const rows = articles.map(article => 
            `"${article.source.name}","${article.title}","${article.description}","${article.publishedAt}","${article.url}"`
        ).join('\n');
        return header + rows;
    }
    
    // Human readable
    let output = '';
    articles.forEach((article, index) => {
        output += `${index + 1}. [${article.source.name}] ${article.title}\n`;
        output += `   📅 ${new Date(article.publishedAt).toLocaleString()}\n`;
        output += `   📝 ${article.description}\n`;
        output += `   🔗 ${article.url}\n\n`;
    });
    
    return output;
}

// Main function
async function main() {
    const args = process.argv.slice(2);
    const command = args[0] || 'top';
    const category = args[1] || 'technology';
    const limit = parseInt(args.find(arg => arg.startsWith('--limit='))?.split('=')[1]) || 5;
    const format = args.find(arg => arg.startsWith('--format='))?.split('=')[1] || 'default';
    
    colorLog(`📰 Google News Scraper (Fallback Mode)`, 'cyan');
    colorLog(`=====================================\n`, 'cyan');
    
    let articles = [];
    
    // Try Google News API first
    if (command === 'top') {
        const apiResult = await tryGoogleAPI('top-headlines', { country: 'us', pageSize: limit });
        if (apiResult && apiResult.articles) {
            articles = apiResult.articles;
        }
    } else if (command === 'topic') {
        const apiResult = await tryGoogleAPI('top-headlines', { category, pageSize: limit });
        if (apiResult && apiResult.articles) {
            articles = apiResult.articles;
        }
    }
    
    // Fallback to RSS if API failed
    if (articles.length === 0) {
        articles = await fetchFromRSS(category, limit);
    }
    
    // Last resort: mock news
    if (articles.length === 0) {
        articles = generateMockNews(category, limit);
    }
    
    // Output results
    colorLog(`📊 Found ${articles.length} articles\n`, 'green');
    console.log(formatOutput(articles, format));
    
    // Save to file for integration with daily briefing
    if (args.includes('--save')) {
        const filename = `${category}-news-${Date.now()}.json`;
        await fs.writeFile(filename, JSON.stringify({ articles }, null, 2));
        colorLog(`💾 Saved to ${filename}`, 'blue');
    }
}

// Run if called directly
if (require.main === module) {
    main().catch(error => {
        colorLog(`❌ Error: ${error.message}`, 'red');
        process.exit(1);
    });
}

module.exports = { main, tryGoogleAPI, fetchFromRSS, generateMockNews };
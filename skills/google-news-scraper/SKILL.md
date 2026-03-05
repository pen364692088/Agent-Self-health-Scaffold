---
name: google-news-scraper
description: Google News Automation Scraper with API integration. Fetches latest news from Google News API with configurable topics, languages, and regions.
user-invocable: true
metadata: {"openclaw": {"emoji": "📰", "requires": {"bins": ["curl", "jq"]}, "os": ["darwin", "linux", "win32"]}}
---

# Google News Automation Scraper Skill

Fetches latest news from Google News API with advanced filtering and automation capabilities.

## Configuration

First, set up your API key:

```bash
export GOOGLE_NEWS_API_KEY="app-ur6S2QXl17jGZrmqr4ssVy3r"
```

Or create a config file:
```bash
mkdir -p ~/.config/google-news-scraper
echo 'GOOGLE_NEWS_API_KEY="app-ur6S2QXl17jGZrmqr4ssVy3r"' > ~/.config/google-news-scraper/config
```

## Usage

### Basic News Fetching

```bash
# Get top headlines
google-news-scraper top

# Get news by topic
google-news-scraper topic technology

# Get news by keyword
google-news-scraper search "artificial intelligence"

# Get news by country
google-news-scraper country us
```

### Advanced Options

```bash
# Get news with specific language
google-news-scraper topic business --language en

# Get news from multiple sources
google-news-scraper sources "techcrunch,verge,wired"

# Get news with sorting
google-news-scraper topic technology --sort publishedAt

# Limit number of articles
google-news-scraper top --limit 10
```

### Categories Available

- business
- entertainment
- general
- health
- science
- sports
- technology

### Countries/Languages

- us (en-US) - United States
- gb (en-GB) - United Kingdom  
- cn (zh-CN) - China
- jp (ja) - Japan
- de (de) - Germany
- fr (fr) - France
- And many more...

## API Endpoints

### Top Headlines
```
GET https://newsapi.org/v2/top-headlines
```

### Everything (Search)
```
GET https://newsapi.org/v2/everything
```

### Sources
```
GET https://newsapi.org/v2/sources
```

## Output Formats

### Default (Human Readable)
```
📰 Top Headlines (US)
=====================

1. [TechCrunch] AI Breakthrough: New Model Achieves Human-Level Performance
   Published: 2 hours ago
   Summary: Researchers announce a breakthrough in AI...

2. [Reuters] Stock Markets Rally on Positive Economic Data
   Published: 3 hours ago  
   Summary: Global markets surged today as...
```

### JSON Format
```bash
google-news-scraper top --format json
```

### CSV Format
```bash
google-news-scraper topic technology --format csv > tech-news.csv
```

## Integration with Daily Briefing

This skill can enhance your existing daily briefing system:

```bash
# Get latest tech news for daily report
google-news-scraper topic technology --limit 5 --format json > daily-tech-news.json

# Get business news
google-news-scraper topic business --limit 3 --format json > daily-business-news.json

# Get AI/ML news
google-news-scraper search "artificial intelligence machine learning" --limit 5 --format json > daily-ai-news.json
```

## Automation

### Cron Job Setup
```bash
# Every morning at 8 AM
0 8 * * * /usr/local/bin/google-news-scraper top --limit 10 >> /path/to/morning-news.log

# Every hour for tech updates
0 * * * * /usr/local/bin/google-news-scraper topic technology --limit 5 >> /path/to/tech-updates.log
```

### Integration with Existing Scripts
```bash
#!/bin/bash
# Enhanced daily briefing with Google News

echo "🔍 Fetching latest news from Google News API..."

# Get top headlines
google-news-scraper top --limit 5 --format json > /tmp/top-headlines.json

# Get category-specific news
google-news-scraper topic technology --limit 3 --format json > /tmp/tech-news.json
google-news-scraper topic business --limit 3 --format json > /tmp/business-news.json

# Merge with existing briefing system
node /path/to/your/daily-briefing/merge-news.js
```

## Error Handling

The skill includes robust error handling for:
- API rate limits (automatic retry with backoff)
- Network connectivity issues
- Invalid API keys
- Malformed responses

## Rate Limits

Free tier: 1,000 requests per day
- Use caching to minimize API calls
- Batch multiple topics in single requests when possible
- Implement smart refresh intervals

## Security Notes

- API key is stored securely in environment variables
- All requests use HTTPS
- No sensitive data is logged
- Input validation prevents injection attacks

## Troubleshooting

### API Key Issues
```bash
# Test API key
curl -H "X-API-Key: $GOOGLE_NEWS_API_KEY" "https://newsapi.org/v2/top-headlines?country=us&pageSize=1"
```

### Network Issues
```bash
# Test connectivity
curl -I https://newsapi.org
```

### Rate Limit Reached
```bash
# Check remaining quota
curl -H "X-API-Key: $GOOGLE_NEWS_API_KEY" "https://newsapi.org/v2/everything?q=test&pageSize=1"
```

## Examples

### Daily Tech Briefing
```bash
google-news-scraper topic technology --limit 5 --sort publishedAt | \
while read line; do
    echo "🤖 $line"
done
```

### Market News Feed
```bash
google-news-scraper topic business --sources "bloomberg,reuters,wsj" --format csv > market-news.csv
```

### AI Research Updates
```bash
google-news-scraper search "artificial intelligence research" --language en --sort publishedAt --limit 10
```
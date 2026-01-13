# SearXNG Meta-Search Engine

SearXNG is a privacy-respecting meta-search engine that aggregates results from multiple search engines without tracking users.

## Features

- **Privacy-focused**: No tracking, no profiling, no ads
- **Meta-search**: Aggregates results from 70+ search engines
- **Self-hosted**: Full control over data and availability
- **JSON API**: Easy integration with automation tools
- **Redis caching**: Fast repeated searches

## Quick Start

### 1. Start SearXNG

```bash
# Start all services
docker-compose up -d

# Check SearXNG is running
docker-compose ps searxng
curl http://localhost:8080
```

### 2. Web Interface

Open http://localhost:8080 in your browser

### 3. API Usage

```bash
# JSON search
curl "http://localhost:8080/search?q=B2B+marketing&format=json"

# With category
curl "http://localhost:8080/search?q=AI+trends&format=json&categories=news"

# With time range
curl "http://localhost:8080/search?q=marketing&format=json&time_range=week"
```

## Search Categories

| Category | Description | Example Query |
|----------|-------------|---------------|
| `general` | General web search | Business trends |
| `news` | News articles | Latest marketing news |
| `social media` | Reddit, Lemmy, etc. | What is trending on reddit |
| `images` | Image search | Marketing infographic examples |
| `videos` | YouTube, Vimeo | Marketing tutorial videos |
| `it` | GitHub, StackOverflow | Marketing automation code |
| `science` | Academic papers | Marketing research papers |

## Available Search Engines

### Enabled by Default

**General Web:**
- Google
- DuckDuckGo
- Bing
- Brave

**News:**
- Google News
- Reddit
- HackerNews

**Social:**
- Reddit
- Lemmy

**Tech:**
- GitHub
- StackOverflow

**Media:**
- YouTube
- Google Images
- Unsplash
- Vimeo

**Academic:**
- Wikipedia
- ArXiv
- Wikidata

## Python Integration

### Basic Usage

```python
from searxng_tool import SearXNGTool

# Initialize
searxng = SearXNGTool(base_url="http://searxng:8080")

# General search
results = searxng.search_general("B2B marketing automation")

for result in results:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Content: {result['content']}\n")
```

### Category-Specific Searches

```python
# News (recent articles)
news = searxng.search_news("AI in marketing", time_range="week")

# Social media (discussions)
social = searxng.search_social("marketing automation")

# Technical content
tech = searxng.search_tech("marketing automation github")

# Academic papers
academic = searxng.search_academic("B2B marketing research")
```

### Advanced Use Cases

#### Competitor Research

```python
# Search for competitor information
results = searxng.competitor_search(
    company_name="Competitor Inc",
    keywords=["pricing", "features", "reviews", "customers"]
)

for keyword, search_results in results.items():
    print(f"\n{keyword.upper()}:")
    for result in search_results[:3]:
        print(f"  - {result['title']}")
```

#### Market Research

```python
# Multi-topic research
results = searxng.market_research(
    industry="B2B SaaS",
    topics=["trends", "challenges", "opportunities", "best practices"]
)

for topic, data in results.items():
    print(f"\n{topic}:")
    print(f"  News: {len(data['news'])} articles")
    print(f"  General: {len(data['general'])} results")
```

#### Trend Detection

```python
# Find trending discussions
trends = searxng.trend_search(
    topic="marketing automation",
    sources=["reddit", "hackernews"]
)

for item in trends[:5]:
    print(f"{item['title']}")
    print(f"Source: {item['engine']}")
    print(f"Date: {item.get('publishedDate', 'N/A')}\n")
```

## LangChain Integration

```python
from langchain.agents import initialize_agent, AgentType
from langchain.llms import Ollama
from searxng_tool import create_searxng_langchain_tool

# Initialize LLM
llm = Ollama(base_url="http://ollama:11434", model="llama3:8b")

# Create SearXNG tool
search_tool = create_searxng_langchain_tool()

# Create agent
agent = initialize_agent(
    tools=[search_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Use agent
result = agent.run("What are the latest trends in B2B marketing automation?")
print(result)
```

## Configuration

### settings.yml

The `settings.yml` file controls:
- Enabled/disabled search engines
- Search categories
- Rate limiting
- Caching behavior
- Privacy settings

Key sections:

```yaml
# Rate limiting
limiter:
  window: 3600
  max_connections: 100

# Redis caching
redis:
  url: redis://redis:6379/2

# Search engines
engines:
  - name: google
    engine: google
    disabled: false
```

### Environment Variables

Set in `.env`:

```bash
# Secret key for sessions
SEARXNG_SECRET=your_random_secret_here
```

Generate secret:
```bash
openssl rand -hex 32
```

## Customization

### Add New Search Engine

Edit `settings.yml`:

```yaml
engines:
  - name: custom_search
    engine: xpath
    search_url: https://example.com/search?q={query}
    url_xpath: //a[@class="result"]/@href
    title_xpath: //a[@class="result"]
    content_xpath: //p[@class="description"]
    shortcut: cs
    disabled: false
```

### Disable Engines

```yaml
engines:
  - name: google
    disabled: true  # Disable Google
```

### Add Custom Categories

```yaml
categories_as_tabs:
  marketing:  # New category

enabled_categories:
  - marketing
```

## Monitoring

### Check Status

```bash
# Health check
curl http://localhost:8080/healthz

# Stats
curl http://localhost:8080/stats

# View logs
docker logs searxng -f

# Check memory usage
docker stats searxng
```

### Metrics

SearXNG exposes metrics at:
- http://localhost:8080/stats/checker
- http://localhost:8080/stats/errors

## Performance Tuning

### Increase Workers

Edit `docker-compose.yml`:

```yaml
searxng:
  environment:
    - UWSGI_WORKERS=8  # Default: 4
    - UWSGI_THREADS=4
```

### Adjust Timeouts

Edit `settings.yml`:

```yaml
outgoing:
  request_timeout: 10.0      # Seconds
  max_request_timeout: 20.0
```

### Cache Configuration

```yaml
redis:
  url: redis://redis:6379/2

# Cache search results for 1 hour
search:
  cache_ttl: 3600
```

## Troubleshooting

### No Results

**Possible causes:**
1. Search engines are down or slow
2. Network connectivity issues
3. Rate limiting by search engines

**Solutions:**
```bash
# Check logs
docker logs searxng

# Test specific engine
curl "http://localhost:8080/search?q=test&format=json&engines=duckduckgo"

# Restart SearXNG
docker-compose restart searxng
```

### Slow Searches

```bash
# Check which engines are slow
docker logs searxng | grep "timeout"

# Disable slow engines in settings.yml
engines:
  - name: slow_engine
    disabled: true
```

### Connection Refused

```bash
# Check if running
docker-compose ps searxng

# Check port binding
docker port searxng

# Restart
docker-compose restart searxng
```

## Privacy & Security

### Privacy Features

- ✅ No user tracking
- ✅ No search history logging
- ✅ No cookies (except session management)
- ✅ Proxy for images (prevents leaking IP to image hosts)
- ✅ URL tracker removal
- ✅ HTTPS support

### Security Checklist

- ✅ Secret key configured (SEARXNG_SECRET)
- ✅ Rate limiting enabled
- ✅ Not exposed to public internet (localhost/internal network only)
- ✅ Regular updates (pull latest image)

### For Production

```yaml
# Add authentication (in settings.yml)
server:
  secret_key: "${SEARXNG_SECRET}"
  limiter: true
  public_instance: false

# Use HTTPS with Nginx reverse proxy
```

## Use Cases in Marketing Platform

### Research Agent
```python
# Find industry trends
results = searxng.search_news("B2B marketing trends 2024", time_range="month")

# Academic research
papers = searxng.search_academic("marketing automation effectiveness")
```

### Competitor Agent
```python
# Monitor competitors
competitor_info = searxng.competitor_search(
    "Competitor Corp",
    ["pricing", "new features", "press releases"]
)
```

### Trend Agent
```python
# Detect trending topics
trends = searxng.trend_search("marketing", sources=["reddit", "hackernews"])

# Sort by engagement
top_trends = sorted(trends, key=lambda x: x.get("score", 0), reverse=True)
```

### Content Agent
```python
# Find content inspiration
examples = searxng.search_general("best B2B blog posts 2024")

# Image search for visuals
images = searxng.search_images("B2B marketing infographic")
```

## Comparison with Alternatives

| Feature | SearXNG | Google Custom Search | Bing Search API |
|---------|---------|---------------------|-----------------|
| **Cost** | Free (self-hosted) | $5/1000 queries | $7/1000 queries |
| **Privacy** | ✅ Complete | ❌ Google tracking | ❌ Microsoft tracking |
| **Rate Limits** | None (self-imposed) | 100 queries/day free | 3 queries/sec |
| **Setup** | Docker | API key | API key |
| **Engines** | 70+ aggregated | Google only | Bing only |

**Recommendation**: Use SearXNG for research and competitor monitoring (free, private, unlimited).

## Additional Resources

- [SearXNG Documentation](https://docs.searxng.org/)
- [List of All Engines](https://docs.searxng.org/admin/engines/index.html)
- [Settings Reference](https://docs.searxng.org/admin/settings/index.html)
- [Public Instances](https://searx.space/) (for inspiration, not recommended for production)

# Redis Configuration and Usage

Redis serves as the caching layer and job queue system for the B2B Marketing Automation Platform.

## Database Allocation

Redis has 16 databases (0-15). We use them as follows:

- **DB 0**: Session cache (agent conversations, temporary state)
- **DB 1**: Content cache (draft content, SEO results)
- **DB 2**: API response cache (search results, competitor data)
- **DB 3**: Job queue (Celery/RQ tasks)
- **DB 4**: Rate limiting counters
- **DB 5-15**: Reserved for future use

## Configuration

The `redis.conf` file is optimized for:
- **Persistence**: AOF + RDB snapshots
- **Memory management**: 2GB limit with LRU eviction
- **Performance**: 4 I/O threads for parallel processing
- **Durability**: `appendfsync everysec` for balanced performance/safety

## Usage Examples

### Python (using redis_manager.py)

```python
from redis_manager import get_redis_manager

# Initialize manager
redis = get_redis_manager()

# Session management
redis.set_session("user_123", {"name": "John", "role": "admin"}, ttl=3600)
session = redis.get_session("user_123")

# Content caching
redis.cache_content("draft_456", "Blog post content here", ttl=86400)
content = redis.get_cached_content("draft_456")

# API response caching
redis.cache_search_results("AI marketing trends", results_list, ttl=3600)
cached = redis.get_cached_search_results("AI marketing trends")

# Job queueing
redis.enqueue_job("content_generation", {"campaign_id": 1, "type": "blog"})
job = redis.dequeue_job("content_generation", timeout=5)

# Rate limiting
allowed = redis.check_rate_limit("api_linkedin", max_requests=100, window_seconds=3600)
if allowed:
    # Make API call
    pass
else:
    # Rate limited
    pass

# Agent conversation memory
redis.store_agent_conversation("campaign_1", "research_agent", conversation_history)
history = redis.get_agent_conversation("campaign_1", "research_agent")
```

### Command Line

```bash
# Connect to Redis
docker exec -it redis redis-cli

# Select database
SELECT 0

# List all keys
KEYS *

# Get value
GET session:user_123

# Monitor commands in real-time
MONITOR

# Check memory usage
INFO memory

# Flush specific database
FLUSHDB

# Check connection
PING
```

## Monitoring

### Check Redis Status

```bash
# View logs
docker logs redis

# Check memory usage
docker exec redis redis-cli INFO memory

# Check connected clients
docker exec redis redis-cli INFO clients

# Check slow queries
docker exec redis redis-cli SLOWLOG GET 10
```

### Metrics to Monitor

- **Memory usage**: Should stay under 2GB
- **Hit rate**: Cache hit/miss ratio
- **Eviction count**: LRU evictions (increase memory if high)
- **Slow log**: Queries > 10ms
- **Connected clients**: Number of active connections

## Performance Tuning

### For High Write Throughput
```conf
# Reduce AOF sync frequency (less durable but faster)
appendfsync no
```

### For Low Latency Reads
```conf
# Increase I/O threads
io-threads 8
```

### For Memory-Constrained Environments
```conf
# Reduce memory limit
maxmemory 1gb

# Use volatile-lru (only evict keys with TTL)
maxmemory-policy volatile-lru
```

## Backup and Restore

### Backup

```bash
# RDB snapshot (manual)
docker exec redis redis-cli BGSAVE

# Copy RDB file
docker cp redis:/data/dump.rdb ./backup/

# Copy AOF file
docker cp redis:/data/appendonly.aof ./backup/
```

### Restore

```bash
# Stop Redis
docker-compose stop redis

# Replace data files
docker cp ./backup/dump.rdb redis:/data/
docker cp ./backup/appendonly.aof redis:/data/

# Start Redis
docker-compose start redis
```

## Common Patterns

### Distributed Locking

```python
import redis
import time

r = redis.Redis(host='redis', port=6379)

# Acquire lock
lock = r.set('lock:campaign_123', 'worker_1', nx=True, ex=30)

if lock:
    try:
        # Critical section
        process_campaign()
    finally:
        # Release lock
        r.delete('lock:campaign_123')
```

### Pub/Sub for Real-Time Updates

```python
# Publisher (n8n workflow)
r = redis.Redis(host='redis', port=6379)
r.publish('content_updates', json.dumps({'draft_id': 123, 'status': 'approved'}))

# Subscriber (Streamlit dashboard)
p = r.pubsub()
p.subscribe('content_updates')

for message in p.listen():
    if message['type'] == 'message':
        data = json.loads(message['data'])
        update_dashboard(data)
```

### Sorted Sets for Leaderboards

```python
# Add content by engagement score
r.zadd('top_content', {'post_123': 450, 'post_124': 320})

# Get top 10
top_10 = r.zrevrange('top_content', 0, 9, withscores=True)
```

## Troubleshooting

### Connection Refused

```bash
# Check if Redis is running
docker-compose ps redis

# Check logs
docker logs redis

# Restart Redis
docker-compose restart redis
```

### Out of Memory

```bash
# Check memory usage
docker exec redis redis-cli INFO memory

# Clear specific database
docker exec redis redis-cli -n 2 FLUSHDB

# Increase memory limit in redis.conf
maxmemory 4gb
```

### Slow Queries

```bash
# View slow queries
docker exec redis redis-cli SLOWLOG GET 20

# Common causes:
# - Large keys (use SCAN instead of KEYS)
# - Complex operations on large sets/lists
# - No TTL on cache entries (memory pressure)
```

## Security Checklist

- ✅ Password protection enabled (REDIS_PASSWORD in .env)
- ✅ Bind to localhost or private network only
- ✅ Protected mode enabled
- ✅ Disable dangerous commands (FLUSHALL, FLUSHDB in production)
- ✅ Use TLS for external connections (if needed)

## Integration with Services

### n8n Workflows
Use Redis nodes for:
- Caching API responses
- Job queuing
- Rate limiting

### LangChain Agents
Use `redis_manager.py` for:
- Agent conversation memory
- Tool result caching
- Shared state across agents

### Streamlit Dashboard
Use Redis for:
- User session management
- Real-time updates via Pub/Sub
- Dashboard data caching

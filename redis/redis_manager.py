"""
Redis Manager for B2B Marketing Automation Platform
Provides helper functions for caching, queuing, and session management
"""

import redis
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import timedelta
import os


class RedisManager:
    """
    Centralized Redis manager with database-specific helpers

    Database allocation:
    - DB 0: Session cache (agent conversations, temporary state)
    - DB 1: Content cache (draft content, SEO results)
    - DB 2: API response cache (search results, competitor data)
    - DB 3: Job queue (Celery/RQ tasks)
    - DB 4: Rate limiting counters
    """

    def __init__(
        self,
        host: str = "redis",
        port: int = 6379,
        password: Optional[str] = None,
        decode_responses: bool = True
    ):
        """Initialize Redis connection pool"""
        self.host = host
        self.port = port
        self.password = password or os.getenv("REDIS_PASSWORD")

        # Create connection pool
        self.pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            password=self.password,
            decode_responses=decode_responses,
            max_connections=50
        )

    def get_client(self, db: int = 0) -> redis.Redis:
        """Get Redis client for specific database"""
        return redis.Redis(connection_pool=self.pool, db=db)

    # ==================== SESSION CACHE (DB 0) ====================

    def set_session(self, key: str, value: Dict, ttl: int = 3600) -> bool:
        """Store session data with TTL (default 1 hour)"""
        client = self.get_client(db=0)
        return client.setex(
            f"session:{key}",
            ttl,
            json.dumps(value)
        )

    def get_session(self, key: str) -> Optional[Dict]:
        """Retrieve session data"""
        client = self.get_client(db=0)
        data = client.get(f"session:{key}")
        return json.loads(data) if data else None

    def delete_session(self, key: str) -> bool:
        """Delete session data"""
        client = self.get_client(db=0)
        return bool(client.delete(f"session:{key}"))

    # ==================== CONTENT CACHE (DB 1) ====================

    def cache_content(self, key: str, content: str, ttl: int = 86400) -> bool:
        """Cache content draft or SEO result (default 24 hours)"""
        client = self.get_client(db=1)
        return client.setex(
            f"content:{key}",
            ttl,
            content
        )

    def get_cached_content(self, key: str) -> Optional[str]:
        """Retrieve cached content"""
        client = self.get_client(db=1)
        return client.get(f"content:{key}")

    def cache_seo_result(self, content_id: str, seo_data: Dict, ttl: int = 86400) -> bool:
        """Cache SEO analysis results"""
        client = self.get_client(db=1)
        return client.setex(
            f"seo:{content_id}",
            ttl,
            json.dumps(seo_data)
        )

    def get_seo_result(self, content_id: str) -> Optional[Dict]:
        """Retrieve cached SEO results"""
        client = self.get_client(db=1)
        data = client.get(f"seo:{content_id}")
        return json.loads(data) if data else None

    # ==================== API RESPONSE CACHE (DB 2) ====================

    def cache_api_response(self, key: str, response: Dict, ttl: int = 3600) -> bool:
        """Cache API responses (search, scraping, etc.)"""
        client = self.get_client(db=2)
        return client.setex(
            f"api:{key}",
            ttl,
            json.dumps(response)
        )

    def get_cached_api_response(self, key: str) -> Optional[Dict]:
        """Retrieve cached API response"""
        client = self.get_client(db=2)
        data = client.get(f"api:{key}")
        return json.loads(data) if data else None

    def cache_search_results(self, query: str, results: List[Dict], ttl: int = 3600) -> bool:
        """Cache search results for 1 hour"""
        return self.cache_api_response(f"search:{query}", {"results": results}, ttl)

    def get_cached_search_results(self, query: str) -> Optional[List[Dict]]:
        """Retrieve cached search results"""
        data = self.get_cached_api_response(f"search:{query}")
        return data.get("results") if data else None

    # ==================== JOB QUEUE (DB 3) ====================

    def enqueue_job(self, queue_name: str, job_data: Dict) -> bool:
        """Add job to queue (FIFO)"""
        client = self.get_client(db=3)
        return bool(client.rpush(
            f"queue:{queue_name}",
            json.dumps(job_data)
        ))

    def dequeue_job(self, queue_name: str, timeout: int = 0) -> Optional[Dict]:
        """Pop job from queue (blocking if timeout > 0)"""
        client = self.get_client(db=3)
        if timeout > 0:
            result = client.blpop(f"queue:{queue_name}", timeout)
            return json.loads(result[1]) if result else None
        else:
            result = client.lpop(f"queue:{queue_name}")
            return json.loads(result) if result else None

    def get_queue_length(self, queue_name: str) -> int:
        """Get number of jobs in queue"""
        client = self.get_client(db=3)
        return client.llen(f"queue:{queue_name}")

    # ==================== RATE LIMITING (DB 4) ====================

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if rate limit is exceeded
        Returns True if allowed, False if rate limited
        """
        client = self.get_client(db=4)
        current = client.get(f"ratelimit:{key}")

        if current is None:
            # First request in window
            client.setex(f"ratelimit:{key}", window_seconds, 1)
            return True

        if int(current) < max_requests:
            # Increment and allow
            client.incr(f"ratelimit:{key}")
            return True

        # Rate limit exceeded
        return False

    def get_rate_limit_status(self, key: str) -> Optional[int]:
        """Get current request count for rate limit key"""
        client = self.get_client(db=4)
        count = client.get(f"ratelimit:{key}")
        return int(count) if count else None

    # ==================== AGENT MEMORY ====================

    def store_agent_conversation(
        self,
        campaign_id: str,
        agent_name: str,
        conversation: List[Dict],
        ttl: int = 86400
    ) -> bool:
        """Store agent conversation history"""
        key = f"agent:{campaign_id}:{agent_name}"
        return self.cache_api_response(key, {"conversation": conversation}, ttl)

    def get_agent_conversation(
        self,
        campaign_id: str,
        agent_name: str
    ) -> Optional[List[Dict]]:
        """Retrieve agent conversation history"""
        key = f"agent:{campaign_id}:{agent_name}"
        data = self.get_cached_api_response(key)
        return data.get("conversation") if data else None

    # ==================== UTILITY METHODS ====================

    def flush_database(self, db: int) -> bool:
        """Flush specific database (use with caution)"""
        client = self.get_client(db=db)
        return client.flushdb()

    def get_keys(self, pattern: str, db: int = 0) -> List[str]:
        """Get all keys matching pattern"""
        client = self.get_client(db=db)
        return client.keys(pattern)

    def ping(self) -> bool:
        """Check Redis connection"""
        try:
            client = self.get_client(db=0)
            return client.ping()
        except Exception:
            return False

    def get_info(self) -> Dict:
        """Get Redis server info"""
        client = self.get_client(db=0)
        return client.info()


# ==================== CONVENIENCE FUNCTIONS ====================

def get_redis_manager() -> RedisManager:
    """Get singleton Redis manager instance"""
    return RedisManager(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD")
    )


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = get_redis_manager()

    # Test connection
    if manager.ping():
        print("✓ Connected to Redis")

        # Show server info
        info = manager.get_info()
        print(f"Redis version: {info.get('redis_version')}")
        print(f"Used memory: {info.get('used_memory_human')}")
    else:
        print("✗ Failed to connect to Redis")

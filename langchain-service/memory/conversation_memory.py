"""
Conversation Memory Manager
Persistent conversation memory using Redis
"""

import redis
import json
from typing import List, Dict, Optional
from datetime import datetime
import structlog

from config import get_redis_url


logger = structlog.get_logger()


class ConversationMemoryManager:
    """
    Manages persistent conversation memory across agents

    Uses Redis DB 0 for session storage
    """

    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(
            get_redis_url(),
            db=0,  # Session cache DB
            decode_responses=True
        )
        logger.info("conversation_memory_initialized")

    def store_conversation(
        self,
        campaign_id: str,
        agent_name: str,
        messages: List[Dict[str, str]],
        ttl: int = 86400  # 24 hours
    ):
        """
        Store conversation history

        Args:
            campaign_id: Campaign identifier
            agent_name: Name of agent
            messages: List of message dicts with 'role' and 'content'
            ttl: Time to live in seconds
        """
        key = f"conversation:{campaign_id}:{agent_name}"

        conversation_data = {
            "campaign_id": campaign_id,
            "agent_name": agent_name,
            "messages": messages,
            "updated_at": datetime.utcnow().isoformat()
        }

        self.redis_client.setex(
            key,
            ttl,
            json.dumps(conversation_data)
        )

        logger.info(
            "conversation_stored",
            campaign_id=campaign_id,
            agent=agent_name,
            message_count=len(messages)
        )

    def get_conversation(
        self,
        campaign_id: str,
        agent_name: str
    ) -> Optional[List[Dict[str, str]]]:
        """
        Retrieve conversation history

        Args:
            campaign_id: Campaign identifier
            agent_name: Name of agent

        Returns:
            List of messages or None if not found
        """
        key = f"conversation:{campaign_id}:{agent_name}"
        data = self.redis_client.get(key)

        if data:
            conversation_data = json.loads(data)
            logger.info(
                "conversation_retrieved",
                campaign_id=campaign_id,
                agent=agent_name,
                message_count=len(conversation_data.get("messages", []))
            )
            return conversation_data.get("messages", [])

        return None

    def append_message(
        self,
        campaign_id: str,
        agent_name: str,
        role: str,
        content: str
    ):
        """
        Append new message to conversation

        Args:
            campaign_id: Campaign identifier
            agent_name: Name of agent
            role: Message role (user/assistant/system)
            content: Message content
        """
        # Get existing conversation
        messages = self.get_conversation(campaign_id, agent_name) or []

        # Append new message
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Store updated conversation
        self.store_conversation(campaign_id, agent_name, messages)

    def delete_conversation(self, campaign_id: str, agent_name: str):
        """
        Delete conversation history

        Args:
            campaign_id: Campaign identifier
            agent_name: Name of agent
        """
        key = f"conversation:{campaign_id}:{agent_name}"
        self.redis_client.delete(key)

        logger.info(
            "conversation_deleted",
            campaign_id=campaign_id,
            agent=agent_name
        )

    def get_all_conversations(self, campaign_id: str) -> Dict[str, List[Dict]]:
        """
        Get all agent conversations for a campaign

        Args:
            campaign_id: Campaign identifier

        Returns:
            Dict mapping agent names to conversation messages
        """
        pattern = f"conversation:{campaign_id}:*"
        keys = self.redis_client.keys(pattern)

        conversations = {}
        for key in keys:
            # Extract agent name from key
            agent_name = key.split(":")[-1]

            data = self.redis_client.get(key)
            if data:
                conversation_data = json.loads(data)
                conversations[agent_name] = conversation_data.get("messages", [])

        logger.info(
            "all_conversations_retrieved",
            campaign_id=campaign_id,
            agent_count=len(conversations)
        )

        return conversations

    def summarize_conversation(
        self,
        campaign_id: str,
        agent_name: str,
        max_messages: int = 10
    ) -> str:
        """
        Get conversation summary (last N messages)

        Args:
            campaign_id: Campaign identifier
            agent_name: Name of agent
            max_messages: Maximum messages to include

        Returns:
            Formatted conversation summary
        """
        messages = self.get_conversation(campaign_id, agent_name) or []

        # Get last N messages
        recent_messages = messages[-max_messages:]

        # Format as string
        summary_parts = []
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            summary_parts.append(f"{role.capitalize()}: {content}")

        return "\n".join(summary_parts)


# Global instance
_memory_manager = None


def get_memory_manager() -> ConversationMemoryManager:
    """Get singleton memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = ConversationMemoryManager()
    return _memory_manager

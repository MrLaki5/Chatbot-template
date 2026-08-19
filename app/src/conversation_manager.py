"""Conversation state management with Redis and PostgreSQL."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

import redis.asyncio as redis
from loguru import logger

from config import Settings


class ConversationManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.redis_client = None

    async def initialize(self):
        # Check if already initialized and connected
        if self.redis_client:
            try:
                await self.redis_client.ping()
                return
            except Exception:
                pass

        # Initialize Redis
        self.redis_client = redis.Redis.from_url(
            f"redis://:{self.settings.REDIS_PASSWORD}"
            f"@{self.settings.REDIS_URL}/{self.settings.REDIS_DB}"
        )

        # Test Redis connection
        try:
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _get_redis_key(self, email: str, conversation_id: str) -> str:
        return f"conversation:{email}:{conversation_id}"

    def _get_conversation_id_from_key(self, redis_key: str) -> str:
        return redis_key.split(":", 2)[-1]

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()

    async def delete_conversation(self, email: str, conversation_id: str) -> bool:
        await self.initialize()

        try:
            # Keys
            redis_key = self._get_redis_key(email, conversation_id)

            # Remove from Redis
            await self.redis_client.delete(redis_key)

            logger.info(f"Deleted conversation {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False

    async def save_msg(
        self,
        email: str,
        conversation_id: str,
        source: str,
        content: str,
        message_type: str = "text",
        ttl_hours: int = 24,
    ) -> bool:
        await self.initialize()

        try:
            # Keys
            redis_key = self._get_redis_key(email, conversation_id)

            if isinstance(content, dict):
                content = json.dumps(content)

            # Create message object
            message_data = {
                "source": source,
                "content": content,
                "message_type": message_type,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            # Add message to Redis list (RPUSH to maintain chronological order)
            pipe.rpush(redis_key, json.dumps(message_data))
            # Set TTL for message history
            pipe.expire(redis_key, timedelta(hours=ttl_hours))
            await pipe.execute()

            logger.debug(f"Saved message from {source} for {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return False

    async def get_message_history(
        self, email: str, conversation_id: str, remove_terminate: bool
    ) -> List[Dict[str, Any]]:
        await self.initialize()
        messages = []

        try:
            # Keys
            redis_key = self._get_redis_key(email, conversation_id)
            redis_messages = await self.redis_client.lrange(redis_key, 0, -1)

            if redis_messages:
                # Redis stores messages in chronological order (RPUSH), so no need to reverse
                for message_json in redis_messages:
                    if isinstance(message_json, bytes):
                        message_json = message_json.decode("utf-8")
                    messages.append(json.loads(message_json))
                    if remove_terminate:
                        messages[-1]["content"] = (
                            messages[-1]["content"].replace("TERMINATE", "").strip()
                        )

                logger.debug(f"Loaded {len(messages)} messages from Redis for " f"{redis_key}")
                return messages

            return messages

        except Exception as e:
            logger.error(f"Failed to get message history: {e}")
            return []

    async def get_all_conversations(self, email: str) -> List[Dict[str, Any]]:
        """Get all conversation IDs and their metadata."""
        await self.initialize()
        conversations = []

        try:
            # Get all conversation keys
            pattern = f"conversation:{email}:*"
            keys = await self.redis_client.keys(pattern)

            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode("utf-8")

                # Extract conversation ID
                conversation_id = self._get_conversation_id_from_key(key)

                # Get conversation metadata
                metadata = await self.get_conversation_metadata(email, conversation_id)
                if metadata:
                    conversations.append(metadata)

            # Sort by updated_at (most recent first)
            conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return conversations

        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return []

    async def get_conversation_metadata(
        self, email: str, conversation_id: str
    ) -> Dict[str, Any] | None:
        """Get metadata for a specific conversation."""
        await self.initialize()

        try:
            redis_key = self._get_redis_key(email, conversation_id)

            # Check if conversation exists
            exists = await self.redis_client.exists(redis_key)
            if not exists:
                return None

            # Get first and last messages for metadata
            first_message_json = await self.redis_client.lindex(redis_key, 0)
            last_message_json = await self.redis_client.lindex(redis_key, -1)
            message_count = await self.redis_client.llen(redis_key)

            if not first_message_json:
                return None

            # Parse first message
            if isinstance(first_message_json, bytes):
                first_message_json = first_message_json.decode("utf-8")
            first_message = json.loads(first_message_json)

            # Parse last message
            last_message = first_message
            if last_message_json and last_message_json != first_message_json:
                if isinstance(last_message_json, bytes):
                    last_message_json = last_message_json.decode("utf-8")
                last_message = json.loads(last_message_json)

            # Generate title from first user message (limit to 50 chars)
            title = "New Conversation"
            if first_message.get("source") == "user":
                content = first_message.get("content", "").strip()
                title = content[:50] + ("..." if len(content) > 50 else "")

            return {
                "id": conversation_id,
                "title": title,
                "message_count": message_count,
                "created_at": first_message.get("created_at"),
                "updated_at": last_message.get("created_at"),
                "first_message": first_message.get("content", "")[:100],  # Preview
            }

        except Exception as e:
            logger.error(f"Failed to get conversation metadata for {conversation_id}: {e}")
            return None

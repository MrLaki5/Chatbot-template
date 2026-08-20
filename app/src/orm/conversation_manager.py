"""Conversation state management on PostgreSQL."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from config import Settings
from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .database import dispose_engine, get_session_factory, init_models
from .models import Conversation, Message

TITLE_MAX_LENGTH = 50
PREVIEW_MAX_LENGTH = 100
DEFAULT_TITLE = "New Conversation"


class ConversationManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.initialized = False

    async def initialize(self):
        """Open the connection pool and make sure the tables are there."""
        if self.initialized:
            return

        try:
            await init_models()
            self.initialized = True
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def close(self):
        await dispose_engine()
        self.initialized = False

    def _build_title(self, source: str, content: str) -> str:
        """Title a conversation after its first message, if a user sent it."""
        if source != "user":
            return DEFAULT_TITLE

        content = content.strip()
        return content[:TITLE_MAX_LENGTH] + ("..." if len(content) > TITLE_MAX_LENGTH else "")

    def _to_metadata(self, conversation: Conversation) -> Dict[str, Any]:
        return {
            "id": conversation.id,
            "title": conversation.title,
            "message_count": conversation.message_count,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "first_message": conversation.first_message,
        }

    async def delete_conversation(self, email: str, conversation_id: str) -> bool:
        try:
            session_factory = get_session_factory()

            async with session_factory() as session:
                async with session.begin():
                    # Messages follow the conversation out via ON DELETE CASCADE
                    result = await session.execute(
                        delete(Conversation).where(
                            Conversation.email == email,
                            Conversation.id == conversation_id,
                        )
                    )

            if not result.rowcount:
                return False

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
    ) -> bool:
        try:
            if isinstance(content, dict):
                content = json.dumps(content)

            now = datetime.now(timezone.utc)
            session_factory = get_session_factory()

            # Create the conversation on the first message, touch it on every one after.
            # Title and preview come from that first message and are then left alone.
            upsert = (
                pg_insert(Conversation)
                .values(
                    email=email,
                    id=conversation_id,
                    title=self._build_title(source, content),
                    first_message=content[:PREVIEW_MAX_LENGTH],
                    message_count=1,
                    created_at=now,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    index_elements=["email", "id"],
                    set_={
                        "message_count": Conversation.message_count + 1,
                        "updated_at": now,
                    },
                )
            )

            async with session_factory() as session:
                # One transaction, so the conversation row and its message commit together
                async with session.begin():
                    await session.execute(upsert)
                    session.add(
                        Message(
                            email=email,
                            conversation_id=conversation_id,
                            source=source,
                            content=content,
                            message_type=message_type,
                            created_at=now,
                        )
                    )

            logger.debug(f"Saved message from {source} for {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return False

    async def get_message_history(
        self, email: str, conversation_id: str, remove_terminate: bool
    ) -> List[Dict[str, Any]]:
        messages = []

        try:
            session_factory = get_session_factory()

            async with session_factory() as session:
                # messages.id is a bigserial, so this is chronological order
                result = await session.execute(
                    select(Message)
                    .where(
                        Message.email == email,
                        Message.conversation_id == conversation_id,
                    )
                    .order_by(Message.id)
                )
                rows = result.scalars().all()

            for row in rows:
                content = row.content
                if remove_terminate:
                    content = content.replace("TERMINATE", "").strip()

                messages.append(
                    {
                        "source": row.source,
                        "content": content,
                        "message_type": row.message_type,
                        "created_at": row.created_at.isoformat(),
                    }
                )

            logger.debug(f"Loaded {len(messages)} messages for conversation {conversation_id}")
            return messages

        except Exception as e:
            logger.error(f"Failed to get message history: {e}")
            return []

    async def get_all_conversations(self, email: str) -> List[Dict[str, Any]]:
        """Get all conversation IDs and their metadata."""
        try:
            session_factory = get_session_factory()

            async with session_factory() as session:
                result = await session.execute(
                    select(Conversation)
                    .where(Conversation.email == email)
                    .order_by(Conversation.updated_at.desc())
                )
                conversations = result.scalars().all()

            return [self._to_metadata(conversation) for conversation in conversations]

        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return []

    async def get_conversation_metadata(
        self, email: str, conversation_id: str
    ) -> Dict[str, Any] | None:
        """Get metadata for a specific conversation."""
        try:
            session_factory = get_session_factory()

            async with session_factory() as session:
                conversation = await session.get(Conversation, (email, conversation_id))

            if conversation is None:
                return None

            return self._to_metadata(conversation)

        except Exception as e:
            logger.error(f"Failed to get conversation metadata for {conversation_id}: {e}")
            return None

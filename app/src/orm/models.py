"""Conversation tables.

One `conversations` row per chat, one `messages` row per turn. The conversation id is
supplied by the client, so it is only unique *within* an email: the primary key is the
pair, which keeps one user's conversations out of another's.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKeyConstraint, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    email: Mapped[str] = mapped_column(String(320), primary_key=True)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Derived from the first message and then left alone
    title: Mapped[str] = mapped_column(Text, nullable=False)
    first_message: Mapped[str] = mapped_column(Text, nullable=False)

    # Kept in step with the messages table by the upsert in ConversationManager.save_msg
    message_count: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        # Serves the conversation list: one user's chats ordered by recency.
        # No DESC needed, Postgres scans a btree backwards just as cheaply.
        Index("ix_conversations_email_updated_at", "email", "updated_at"),
    )


class Message(Base):
    __tablename__ = "messages"

    # A bigserial, so ordering by it is insertion order within a conversation
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(64), nullable=False)

    source: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["email", "conversation_id"],
            ["conversations.email", "conversations.id"],
            ondelete="CASCADE",
        ),
        Index("ix_messages_conversation", "email", "conversation_id", "id"),
    )

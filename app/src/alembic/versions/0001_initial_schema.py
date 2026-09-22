"""Initial schema baseline

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-22 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("first_message", sa.Text(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("email", "id"),
    )
    op.create_index("ix_conversations_email_updated_at", "conversations", ["email", "updated_at"])

    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["email", "conversation_id"],
            ["conversations.email", "conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation", "messages", ["email", "conversation_id", "id"])


def downgrade() -> None:
    # Indexes go with their tables
    op.drop_table("messages")
    op.drop_table("conversations")

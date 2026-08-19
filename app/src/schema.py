from typing import Any, Dict, Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for a user query."""

    query: str
    email: str
    note_id: Optional[str] = None
    conversation_id: Optional[str] = None
    command: Optional[str] = None


class StreamEventResponse(BaseModel):
    """Response model for a streaming event."""

    type: str
    data: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    delta: Optional[str] = None
    errorText: Optional[str] = None
    messageId: Optional[str] = None
    toolCallId: Optional[str] = None
    toolName: Optional[str] = None


class ConversationMetadata(BaseModel):
    """Model for conversation metadata."""

    id: str
    title: str
    message_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    first_message: Optional[str] = None


class ConversationListResponse(BaseModel):
    """Response model for conversation list."""

    conversations: list[ConversationMetadata]
    total: int


class ConversationDetailResponse(BaseModel):
    """Response model for conversation details."""

    conversation: ConversationMetadata
    messages: list[Dict[str, Any]]

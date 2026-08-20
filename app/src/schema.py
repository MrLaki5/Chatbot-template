import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator

EMAIL_PATTERN = re.compile(r"^[^\s@:]+@[^\s@:]+$")


class QueryRequest(BaseModel):
    """Request model for a user query."""

    query: str
    conversation_id: Optional[str] = None
    command: Optional[str] = None


class SessionRequest(BaseModel):
    """Request model for creating a session."""

    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Invalid email address")
        return value


class SessionResponse(BaseModel):
    """Response model for the current session."""

    email: str


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

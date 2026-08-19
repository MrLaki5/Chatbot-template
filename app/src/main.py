import json
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from agent import StreamingAgent
from config import settings
from conversation_manager import ConversationManager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from schema import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMetadata,
    QueryRequest,
    StreamEventResponse,
)


@asynccontextmanager
async def lifespan(_app):
    # Startup
    logger.info("Starting service...")

    yield

    # Shutdown
    logger.info("Shutting down service...")
    await agent.close()


app = FastAPI(lifespan=lifespan)
conversation_manager = ConversationManager(settings)
agent = StreamingAgent(
    model=settings.MODEL_NAME,
    system_message=settings.SYSTEM_PROMPT,
    base_url=settings.MODEL_BASE_URL,
    api_key=settings.MODEL_API_KEY,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_chat_ui():
    """Serve the chat UI HTML page."""
    return FileResponse("static/index.html")


@app.get(
    "/conversations/{email}",
    response_model=ConversationListResponse,
    summary="List all conversations",
)
async def get_conversations(email: str):
    """Get list of all conversations with metadata."""
    try:
        conversations_data = await conversation_manager.get_all_conversations(email)
        conversations = [ConversationMetadata(**conv) for conv in conversations_data]

        return ConversationListResponse(conversations=conversations, total=len(conversations))
    except Exception as e:
        logger.error(f"Failed to get conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")


@app.get(
    "/conversations/{email}/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation details",
)
async def get_conversation(email: str, conversation_id: str):
    """Get details of a specific conversation including all messages."""
    try:
        # Get metadata
        metadata_data = await conversation_manager.get_conversation_metadata(
            email, conversation_id
        )
        if not metadata_data:
            raise HTTPException(
                status_code=404, detail=f"Conversation {conversation_id} not found"
            )

        # Get messages
        messages = await conversation_manager.get_message_history(email, conversation_id, False)

        metadata = ConversationMetadata(**metadata_data)

        return ConversationDetailResponse(conversation=metadata, messages=messages)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@app.delete("/conversations/{email}/{conversation_id}", summary="Reset/Delete a conversation")
async def delete_conversation(email: str, conversation_id: str):
    """Delete/reset a specific conversation."""
    try:
        success = await conversation_manager.delete_conversation(email, conversation_id)
        if success:
            logger.info(f"Conversation deleted: {conversation_id}")
            return {
                "success": True,
                "message": f"Conversation {conversation_id} deleted successfully",
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Conversation {conversation_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


@app.post(
    "/conversations/query",
    response_model=StreamEventResponse,
    summary="Stream conversation events",
    description=(
        "Streams real-time events for a conversation. "
        "It will return a conversation id as the first event, which can be "
        "sent back in the request after the first user query."
    ),
)
async def stream_conversation(req: QueryRequest):
    """Stream a conversation with a user."""
    try:
        # If conversation_id is not provided, generate a new one
        conversation_id = req.conversation_id or str(uuid.uuid4())

        # Save user message to history
        await conversation_manager.save_msg(
            email=req.email,
            conversation_id=conversation_id,
            source="user",
            content=req.query,
            message_type="TextMessage",
        )

        # Get conversation history, which now ends with the query above
        messages = await conversation_manager.get_message_history(req.email, conversation_id, True)

        def part(payload: dict) -> str:
            """Frame one part of the AI SDK data stream as a server-sent event."""
            return "data: " + json.dumps(payload) + "\n\n"

        async def event_generator() -> AsyncGenerator[str, None]:
            """Emit the answer as an AI SDK data stream (x-vercel-ai-ui-message-stream v1)."""
            message_id = str(uuid.uuid4())
            text_id = f"text_{uuid.uuid4().hex[:16]}"
            chunks = []
            text_open = False
            error_text = None

            yield part({"type": "start", "messageId": message_id})
            yield part({"type": "start-step"})
            yield part(
                {
                    "type": "data-conversation",
                    "data": {"conversationId": conversation_id},
                }
            )

            try:
                yield part(
                    {
                        "type": "data-agent",
                        "data": {"agent": agent.name, "textId": text_id},
                    }
                )
                yield part({"type": "text-start", "id": text_id})
                text_open = True

                async for delta in agent.run_stream(history=messages):
                    chunks.append(delta)
                    yield part({"type": "text-delta", "id": text_id, "delta": delta})

                yield part({"type": "text-end", "id": text_id})
                text_open = False

                # Save the answer so it comes back as history on the next turn
                answer = "".join(chunks)
                if answer:
                    await conversation_manager.save_msg(
                        email=req.email,
                        conversation_id=conversation_id,
                        source=agent.name,
                        content=answer,
                        message_type="TextMessage",
                    )

                yield part({"type": "finish-step"})
                yield part({"type": "finish"})
            except Exception as e:
                # Not a bare finally: a client disconnect raises GeneratorExit here,
                # and yielding while closing would break the generator
                logger.exception(e)
                logger.error(f"Error during streaming: {str(e)}")
                error_text = str(e)

            if error_text is not None:
                # A text part left open has to be closed before the error part
                if text_open:
                    yield part({"type": "text-end", "id": text_id})
                yield part({"type": "error", "errorText": error_text})

            # The protocol terminates with [DONE], on the error path too
            yield "data: [DONE]\n\n"

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "x-vercel-ai-ui-message-stream": "v1",
        }
        return StreamingResponse(
            event_generator(), media_type="text/event-stream", headers=headers
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(e)
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

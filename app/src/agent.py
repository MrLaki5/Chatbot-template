"""A single streaming chat agent on the OpenAI SDK.

Works against any OpenAI-compatible endpoint (OpenAI, Azure, vLLM, Ollama,
LiteLLM, ...) by pointing `base_url` at it.
"""

from typing import Any, AsyncGenerator, Dict, List, Sequence

from openai import AsyncOpenAI


class StreamingAgent:
    """Answers a conversation as a stream of text deltas."""

    def __init__(
        self,
        model: str,
        system_message: str,
        base_url: str = None,
        api_key: str = None,
        name: str = "Assistant",
    ):
        self.model = model
        self.system_message = system_message
        self.name = name
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    def build_messages(
        self, history: Sequence[Dict[str, Any]] = (), query: str = None
    ) -> List[Dict[str, str]]:
        """Turn stored history into OpenAI chat messages.

        `history` is what ConversationManager.get_message_history returns:
        dicts with a "source" ("user" or an agent name) and "content".
        Pass `query` only if the new user message is not already in `history`.
        """
        messages = [{"role": "system", "content": self.system_message}]

        for message in history:
            content = message.get("content")
            if not content:
                continue
            role = "user" if message.get("source") == "user" else "assistant"
            messages.append({"role": role, "content": content})

        if query:
            messages.append({"role": "user", "content": query})

        return messages

    async def run_stream(
        self, history: Sequence[Dict[str, Any]] = (), query: str = None
    ) -> AsyncGenerator[str, None]:
        """Yield the answer one delta at a time."""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=self.build_messages(history, query),
            stream=True,
        )

        async for chunk in stream:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield content

    async def close(self):
        await self.client.close()

# Chatbot Template
Template repository for chatbot applications

## Features
- **Streaming Responses**: Tokens are streamed to the browser as server-sent events, following the [AI SDK Data Stream Protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol), so any Vercel AI SDK client can consume it as-is
- **Any OpenAI-Compatible Model**: Point `MODEL_BASE_URL` at OpenAI, Azure, vLLM, Ollama, LiteLLM or anything else speaking the same API
- **Configurable Agent**: A single agent driven by the `SYSTEM_PROMPT` setting, no framework in between
- **Email Sessions**: The UI asks for an email on first visit and keeps it in a signed, `HttpOnly` session cookie; every endpoint reads the caller's address from the session rather than the URL or request body
- **Conversation History**: Chats are stored per user in Postgres and kept until deleted, so a conversation can be resumed after a restart
- **Built-in Chat UI**: Dark web interface served by the app itself, with markdown rendering, code highlighting and a conversation sidebar
- **RESTful API**: Clean FastAPI endpoints for integration
- **HTTPS Out of the Box**: nginx reverse proxy that self-signs a certificate on first start, with a Let's Encrypt flow for production
- **Docker Deployment**: Complete containerized setup

## Dependencies
- Docker & Docker Compose
- API key for an OpenAI-compatible endpoint (OpenAI by default)

## Architecture

```mermaid
flowchart LR
    browser(["Browser<br/>chat UI"])

    subgraph stack["docker compose"]
        nginx["<b>nginx</b><br/>80 redirect · 443 TLS<br/>proxy_buffering off"]
        app["<b>app</b><br/>FastAPI + uvicorn :8013<br/>StreamingAgent<br/>signed session cookie"]
        db[("<b>postgres</b><br/>conversations · messages<br/>kept until deleted")]
    end

    model["<b>OpenAI-compatible endpoint</b><br/>MODEL_BASE_URL<br/>OpenAI · Azure · vLLM · Ollama"]

    browser <==>|"HTTPS · SSE token stream"| nginx
    nginx <==>|"proxied to :8013"| app
    app <==>|"chat.completions, stream=true"| model
    app <-->|"read history, save reply"| db
```

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Serves the chat UI |
| `POST /session` | Starts a session from an email and sets the session cookie |
| `GET /session` | Returns the session's email, `401` if there is none |
| `DELETE /session` | Clears the session |
| `POST /conversations/query` | Sends a message, streams the answer back as SSE |
| `GET /conversations` | Lists the session user's conversations |
| `GET /conversations/{conversation_id}` | Loads one conversation with its messages |
| `DELETE /conversations/{conversation_id}` | Deletes a conversation |

Everything under `/conversations` requires a session and answers `401` without one.

### Streaming Protocol

`POST /conversations/query` implements the
[AI SDK Data Stream Protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol)
(`x-vercel-ai-ui-message-stream: v1`), so the bundled UI can be swapped for a Vercel AI SDK
frontend such as `useChat` without touching the backend. One turn looks like this:

```text
data: {"type":"start","messageId":"..."}
data: {"type":"start-step"}
data: {"type":"data-conversation","data":{"conversationId":"..."}}
data: {"type":"data-agent","data":{"agent":"Assistant","textId":"text_..."}}
data: {"type":"text-start","id":"text_..."}
data: {"type":"text-delta","id":"text_...","delta":"Hello"}
data: {"type":"text-end","id":"text_..."}
data: {"type":"finish-step"}
data: {"type":"finish"}
data: [DONE]
```

`data-conversation` and `data-agent` are custom `data-*` parts of the protocol: the first hands
back the conversation id to send with the next request, the second names the agent that is
answering. If the model fails part way through, the open text part is closed and an
`{"type":"error","errorText":"..."}` part is sent, and the stream still terminates with `[DONE]`.

## Quick Start

### 1. Clone and Setup
```bash
git clone git@github.com:MrLaki5/Chatbot-template.git
cd chatbot-template
```

### 2. Pre-commit Setup
Once installed, pre-commit will automatically run on every `git commit`. If any hooks fail, the commit will be rejected and you'll need to fix the issues before committing again.
```bash
pip install pre-commit
pre-commit install
```

### 3. Environment Configuration
Create a `.env` file with your API keys:
```env
MODEL_API_KEY=your_OPENAI_API_KEY_here
```

### 4. Start Services
```bash
docker compose up -d --build
```
Website accessible at [https://localhost](https://localhost)

### 5. (Optional) Reset the database
Drops both tables and creates them again, empty. Every stored conversation is lost.
```bash
docker exec cb_template_app python scripts/init_db.py
```

### 6. (In deployment) Set SSL certificate
* When domain has been acquired, replace the `example.com` domain inside the following files with the acquired domain:
    * [Lets Encrypt certificate generation](nginx/letsencrypt_cert_gen.sh)
    * [Nginx configuration](nginx/nginx_letsencrypt.conf)
* When instance has been deployed, run the following
```bash
docker exec cb_template_nginx /bin/bash -c "./lets_enc.sh"
```

## References
- [AI SDK Data Stream Protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol) - the wire format `/conversations/query` follows
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat) - the model API the agent speaks

# PydanticAI Streaming Cheatsheet

## Basic Streaming Setup

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse

# Create agent
model = OpenAIModel("gpt-4o")
agent = Agent(model, system_prompt="You are a helpful assistant.")
```

## Text Streaming (Complete Text)

```python
async def stream_text():
    async with agent.run_stream("Tell me about AI") as result:
        async for text in result.stream_text():
            print(text)  # Each text contains the full response so far
```

## Delta Streaming (Only New Text)

```python
async def stream_delta():
    async with agent.run_stream("Tell me about AI") as result:
        async for delta in result.stream_text(delta=True):
            print(delta, end="")  # Each delta contains only the new text
```

## Message History Management

```python
async def stream_with_history(message_history):
    # When using delta=True, final message isn't added automatically
    full_response = ""
    async with agent.run_stream("Tell me more", message_history=message_history) as result:
        async for delta in result.stream_text(delta=True):
            full_response += delta
            yield delta
    
    # Manually add to history
    message_history.append({"role": "user", "content": "Tell me more"})
    message_history.append({"role": "assistant", "content": full_response})
```

## Structured Data Streaming

```python
from typing import TypedDict

class UserProfile(TypedDict):
    name: str
    age: int
    bio: str

async def stream_structured():
    async with agent.run_stream(
        "Create a profile for John, age 30, bio: Developer from NYC",
        output_type=UserProfile
    ) as result:
        async for response in result.stream_structured():
            # Get partial validation as it builds
            profile = result.validate_structured_output(UserProfile, allow_partial=True)
            if profile:
                print(f"Partial profile: {profile}")
```

## FastAPI HTTP Streaming

```python
app = FastAPI()

@app.post("/stream")
async def stream_response(query: str):
    return StreamingResponse(
        generate_stream(query),
        media_type="text/event-stream"
    )

async def generate_stream(query: str):
    async with agent.run_stream(query) as result:
        async for delta in result.stream_text(delta=True):
            yield f"data: {json.dumps({'delta': delta})}\n\n"
```

## WebSocket Streaming

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Get message from client
        data = await websocket.receive_json()
        query = data["query"]
        
        # Stream response
        async with agent.run_stream(query) as result:
            async for delta in result.stream_text(delta=True):
                await websocket.send_json({"delta": delta})
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()
```

## MCP Server Streaming

```python
from pydantic_ai.mcp import MCPServerStdio

# Configure environment
env = {
    "API_KEY": "your-api-key",
    "ROOT_FOLDER": "./data/projects"
}

# Create MCP servers
mcp_servers = [
    MCPServerStdio('python', ['project_tools.py'], env=env),
]

# Create agent with MCP servers
agent = Agent(model, mcp_servers=mcp_servers, system_prompt="You are a helpful assistant.")

# Stream with MCP servers
async def stream_with_mcp():
    async with agent.run_mcp_servers():
        async with agent.run_stream("Create a file called hello.txt") as result:
            async for delta in result.stream_text(delta=True):
                print(delta, end="")
```

## Error Handling with Retries

```python
async def stream_with_retries(query, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with agent.run_stream(query) as result:
                async for delta in result.stream_text(delta=True):
                    yield delta
                return  # Success, exit function
        except Exception as e:
            if attempt == max_retries - 1:
                yield f"Error: {str(e)}"
            await asyncio.sleep(1)  # Wait before retry
```

## Context Management Best Practices

```python
async def proper_context_management():
    # Always use both context managers
    async with agent.run_mcp_servers():  # First context manager for MCP servers
        async with agent.run_stream("Hello") as result:  # Second for streaming
            async for delta in result.stream_text(delta=True):
                yield delta
```

## Stream Events for Client Signaling

```python
async def stream_with_events():
    # Send events to help client understand stream state
    yield f"data: {json.dumps({'event': 'start'})}\n\n"
    
    async with agent.run_stream("Tell me about AI") as result:
        async for delta in result.stream_text(delta=True):
            yield f"data: {json.dumps({'delta': delta})}\n\n"
    
    yield f"data: {json.dumps({'event': 'end'})}\n\n"
```

## Common Issues and Solutions

1. **Connection Leaks**: Always use proper context managers (`async with`)

2. **Missing Final Message**: When using delta=True, manually append final message to history

3. **Error Handling**: Implement retry mechanisms and proper error responses

4. **Partial Validation**: Use TypedDict for better partial validation support

5. **Tool Calls During Streaming**: Add special handling for tool calls in stream

6. **WebSocket Management**: Include heartbeats and proper cleanup

7. **Performance**: Use delta streaming for better responsiveness
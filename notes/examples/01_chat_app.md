# Chat App Example with PydanticAI and FastAPI

## Overview

The PydanticAI documentation includes an example of a chat application built with FastAPI. This example demonstrates several key features that are relevant to the XSUS project:

1. **Chat History Management**: Storing and reusing chat history between requests
2. **Message Serialization**: Converting messages to a format suitable for storage and transmission
3. **Response Streaming**: Streaming responses from the LLM to the client in real-time

## Architecture

The example chat app consists of three main components:

1. **FastAPI Backend**: Handles HTTP requests, manages the agent, and streams responses
2. **HTML Frontend**: Simple interface for user interactions
3. **TypeScript Client**: Manages rendering messages and handling streaming updates

## Key Implementation Patterns

### Agent Setup

```python
def get_agent():
    """Get or create the agent instance"""
    model = OpenAIModel(get_default_model())
    return Agent(model, system_prompt="You are a helpful assistant.")
```

### Message History Management

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    agent = get_agent()
    
    # Load message history from request
    message_history = parse_message_history(request.history)
    
    # Run the agent with the message history
    result = await agent.run(request.message, message_history=message_history)
    
    # Add new messages to history
    updated_history = message_history + result.new_messages()
    
    # Return the full response
    return ChatResponse(
        message=result.output,
        history=serialize_message_history(updated_history)
    )
```

### Streaming Implementation

```python
@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    agent = get_agent()
    
    # Parse message history
    message_history = parse_message_history(request.history)
    
    # Create streaming response
    return StreamingResponse(
        stream_agent_response(agent, request.message, message_history),
        media_type="text/event-stream"
    )

async def stream_agent_response(agent, message, history):
    async with agent.run_stream(message, message_history=history) as result:
        # Stream as server-sent events
        async for delta in result.stream_text(delta=True):
            yield f"data: {json.dumps({'delta': delta})}\n\n"
```

## Relevance to XSUS

The XSUS project implements a more sophisticated version of this chat application pattern with additional features:

1. **Database Storage**: Chat sessions and messages are stored in a PostgreSQL database
2. **User Authentication**: Adds authentication and user-specific chat sessions
3. **Agent Selection**: Allows selecting different agents for different chat sessions
4. **WebSocket Support**: Uses WebSockets for more efficient streaming

The core patterns remain similar though, with message history management and streaming being key components of both implementations.

## Implementation Notes

1. **SSE vs WebSockets**: The example uses Server-Sent Events (SSE) for streaming, while XSUS uses both SSE and WebSockets

2. **Frontend Integration**: The way streaming updates are handled in the frontend is similar between the example and XSUS

3. **Error Handling**: Both implementations need to handle errors during streaming gracefully

4. **Message History**: Proper management of message history is crucial for maintaining context in conversations
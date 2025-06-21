# Common Streaming Issues and Solutions in PydanticAI

## Connection Management Issues

### Problem: Connection Leaks

One of the most common issues with streaming in PydanticAI is connection leaks, where resources are not properly cleaned up after streaming completes or errors occur.

### Solution: Context Managers

```python
# Correct usage with proper cleanup
async with agent.run_mcp_servers():
    async with agent.run_stream(user_input) as result:
        async for text in result.stream_text():
            # Process text
```

The double async context manager ensures both MCP servers and streaming connections are properly initialized and cleaned up.

## Streaming Performance Issues

### Problem: Slow Response Times

Large responses can cause delays in first content appearing to users.

### Solution: Delta Streaming and Buffer Management

```python
# Use delta streaming for more responsive UI
async for delta in result.stream_text(delta=True):
    # Send delta immediately to client
    yield f"data: {json.dumps({'delta': delta})}\n\n"
```

## Error Handling Issues

### Problem: Errors During Streaming

Errors that occur during streaming can be difficult to handle gracefully.

### Solution: Try/Except with Reconnection Logic

```python
async def stream_with_retries(agent, user_input, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with agent.run_stream(user_input) as result:
                async for text in result.stream_text():
                    yield text
                break  # Success, exit the retry loop
        except Exception as e:
            if attempt == max_retries - 1:
                yield f"Sorry, an error occurred: {str(e)}"
            await asyncio.sleep(1)  # Brief delay before retry
```

## Message History Issues

### Problem: Missing Final Message

When using `delta=True` with `stream_text()`, the final output message is not added to the result messages.

### Solution: Manual Message Addition

```python
async def stream_and_save_history(agent, user_input, message_history):
    async with agent.run_stream(user_input, message_history=message_history) as result:
        full_response = ""
        async for delta in result.stream_text(delta=True):
            full_response += delta
            yield delta
        
        # Manually add the final message to history
        message_history.append({"role": "user", "content": user_input})
        message_history.append({"role": "assistant", "content": full_response})
```

## Tool Call Issues During Streaming

### Problem: Handling Tool Calls During Streaming

Tool calls during streaming can break the flow of text coming to the client.

### Solution: Stream Markers and Client-Side Handling

```python
async def stream_with_tool_markers(agent, user_input):
    async with agent.run_stream(user_input) as result:
        # Begin streaming
        yield "stream_start\n"
        
        # Stream the text with tool markers
        try:
            async for text in result.stream_text():
                # Check if tool calls are happening
                if result._current_tool_call:
                    yield f"tool_call_start: {result._current_tool_call.name}\n"
                yield text
        except Exception as e:
            if "not text" in str(e):
                # This happens when the model decides to call a tool instead
                yield f"switched_to_tool\n"
            else:
                raise
                
        yield "stream_end\n"
```

## Structured Data Streaming Issues

### Problem: Partial Validation Limitations

Not all types are supported with partial validation in Pydantic, making it challenging to stream structured data.

### Solution: Use TypedDict or SimpleNamespaces

```python
# Using TypedDict instead of complex Pydantic models
from typing import TypedDict

class UserProfile(TypedDict):
    name: str
    bio: str
    location: str

# In streaming code
async for response in result.stream_structured():
    validated = result.validate_structured_output(
        UserProfile,  # Use TypedDict
        allow_partial=True
    )
    if validated:
        yield f"Partial profile: {validated}\n"
```

## WebSocket Streaming Issues

### Problem: WebSocket Connection Management

WebSocket connections can be more challenging to manage than HTTP streaming.

### Solution: Heartbeats and Error Handling

```python
async def websocket_stream(websocket, agent, user_input):
    # Setup heartbeat task
    heartbeat_task = asyncio.create_task(send_heartbeats(websocket))
    
    try:
        async with agent.run_stream(user_input) as result:
            async for delta in result.stream_text(delta=True):
                await websocket.send_json({"type": "delta", "content": delta})
    except Exception as e:
        await websocket.send_json({"type": "error", "content": str(e)})
    finally:
        # Clean up heartbeat task
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

async def send_heartbeats(websocket, interval=30):
    while True:
        await asyncio.sleep(interval)
        try:
            await websocket.send_json({"type": "heartbeat"})
        except:
            break
```

## Issues in XSUS Implementation

The XSUS project has implemented several solutions to common streaming issues:

1. **Error Recovery**: The chat endpoints include retry logic for handling temporary failures

2. **Connection Pooling**: The agent manager maintains a pool of agent instances to reduce initialization overhead

3. **WebSocket Enhancement**: WebSocket connections are enhanced with heartbeats and graceful error handling

4. **Message Buffering**: Messages are buffered on the client side to handle network variability

Despite these solutions, streaming reliability remains a challenging aspect of the system, requiring careful monitoring and maintenance.
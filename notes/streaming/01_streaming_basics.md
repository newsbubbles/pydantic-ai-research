# Streaming in PydanticAI

## Streaming Basics

Streaming is a critical feature in LLM applications that allows for real-time display of model responses as they are generated, rather than waiting for the complete response. PydanticAI provides robust support for streaming both text and structured data.

## Streaming Challenges

PydanticAI addresses two main challenges with streamed results:

1. **Validating Incomplete Data**: Through "partial validation" in Pydantic, allowing structured responses to be validated before they're complete

2. **Response Detection**: PydanticAI streams just enough of a response to determine if it's a tool call or an output, then continues streaming appropriately

## Text Streaming

Basic text streaming in PydanticAI works as follows:

```python
async def main():
    # Configure the agent
    agent = Agent(model, system_prompt="You are a helpful assistant.")
    
    # Start a streaming run
    async with agent.run_stream("Tell me about the history of AI") as result:
        # Process each chunk of text as it arrives
        async for text in result.stream_text():
            print(text, end="\r")
            await asyncio.sleep(0.01)  # Small delay for display
```

The `stream_text()` method yields the complete text response extended as new data is received.

## Delta Streaming

For more efficient streaming, PydanticAI supports delta streaming, where only the new text is yielded:

```python
async for delta in result.stream_text(delta=True):
    print(delta, end="")
    await asyncio.sleep(0.01)
```

## Structured Data Streaming

PydanticAI also supports streaming of structured data:

```python
async for response in result.stream_structured():
    # response is a ModelResponse object
    print(f"Partial response: {response}")

# Validate at the end or during streaming
validated_output = result.validate_structured_output(allow_partial=True)
```

## Streaming in XSUS

The XSUS project extensively uses streaming for its chat interface. The main implementation is in the `backend/app/api/chat_streaming.py` and `backend/app/api/streamlined_chat_streaming.py` files.

The chat streaming implementation follows this general pattern:

1. **Agent Run**: Start an agent run with streaming enabled
2. **FastAPI Response**: Use FastAPI's StreamingResponse to send chunks to the client
3. **WebSocket Support**: Additionally implements WebSocket for more efficient streaming

Example pattern from XSUS (simplified):

```python
@router.post("/chat/{session_id}/stream")
async def stream_chat(session_id: str, message: UserMessage, user: User = Depends(get_current_user)):
    # Get or create chat session
    chat_session = await get_chat_session(db, session_id, user.id)
    
    # Get the agent for this session
    agent = await get_agent_instance(chat_session.agent)
    
    # Load message history
    message_history = await load_message_history(db, chat_session.id)
    
    # Create a streaming response
    return StreamingResponse(
        stream_agent_response(agent, message.content, message_history),
        media_type="text/event-stream"
    )

async def stream_agent_response(agent, user_message, message_history):
    async with agent.run_stream(user_message, message_history=message_history) as result:
        async for delta in result.stream_text(delta=True):
            yield f"data: {json.dumps({'delta': delta})}\n\n"
```

## Issues and Challenges

Common issues with streaming in PydanticAI include:

1. **Connection Management**: Ensuring proper setup and teardown of streaming connections

2. **Partial Validation Limitations**: Not all types are supported with partial validation in Pydantic

3. **Message History**: The final output message is not added to result messages when using delta streaming

4. **Error Handling**: Streaming requires careful error handling as validation errors may occur at any point
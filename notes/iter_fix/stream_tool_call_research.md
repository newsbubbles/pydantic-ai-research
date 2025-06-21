# PydanticAI Agent Stream Tool Call Issue Research

## Problem Overview

When using Claude 3 Haiku with PydanticAI in streaming mode, the model makes tool calls but does not produce a final response after receiving the tool result. This problem specifically occurs when using `run_stream()` with text delta streaming.

## Key Findings from Research

### 1. Streaming Behavior in PydanticAI

From the [documentation](https://ai.pydantic.dev/results/#streamed-results) and [GitHub issue #640](https://github.com/pydantic/pydantic-ai/issues/640):

> "PydanticAI streams just enough of the response to sniff out if it's a tool call or a result, then streams the whole thing and calls tools, or returns the stream as a StreamedRunResult."

This suggests that when using streaming, the library has a different flow for handling tool calls vs. regular responses.

### 2. Delta vs. Non-Delta Streaming

The issue appears specifically when using delta streaming (`delta=True` in the `stream_text()` method). In the current code:

```python
async with agent.run_stream(user_input, message_history=filtered_messages) as result_stream:
    # Use delta streaming to show output as it's generated
    async for delta in result_stream.stream_text(delta=True):
        print(delta, end="", flush=True)
        complete_response += delta
```

When using delta streaming, the agent might be handling the token stream differently than with regular (non-delta) streaming.

### 3. Model-Specific Behaviors

Different models may handle streaming and tool calls differently:

- Claude models (like Claude 3 Haiku) appear more likely to stop after a tool call when streaming.
- OpenAI models may be more consistent about providing final responses after tool calls.

### 4. Message History Handling

From the logs, we can see that the complete response length is 0 after the tool call:

```
2025-06-20 18:54:54,803 - agent_test_fixed - INFO - Complete response received, length: 0
```

This indicates that while the tool call was made, no text content was returned after the tool call completed.

## Potential Solutions

### 1. Use Non-Delta Streaming

Modify the code to use the non-delta version of streaming, which might handle tool call results differently:

```python
async with agent.run_stream(user_input, message_history=filtered_messages) as result_stream:
    # Use non-delta streaming
    async for text in result_stream.stream_text(delta=False):
        print(text, end="", flush=True)
        complete_response = text  # Keep the full response so far
```

### 2. Use Regular `run()` or `run_sync()` for Tool Call Scenarios

If streaming with tool calls is problematic, consider using the non-streaming versions which might handle tool calls and final responses more reliably:

```python
# Use run_sync for tool calls
result = agent.run_sync(user_input, message_history=filtered_messages)
print(result.output)
```

### 3. Manually Request a Follow-up Summary After Tool Call

If we detect that a tool call was made and no final summary was produced, we could make a follow-up request:

```python
async with agent.run_stream(...) as result_stream:
    # Stream the first response
    ...
    
    # If the response was only a tool call (detected by metadata or length)
    if tool_call_only_response:
        # Make a follow-up request to summarize the tool output
        follow_up = agent.run_sync("Please explain what the tool results show.", message_history=result_stream.all_messages())
        print(follow_up.output)
```

### 4. Modify Stream Handling to Capture and Process Tool Calls

Implement a more detailed streaming handler that processes different event types properly:

```python
async with agent.run_stream(...) as result_stream:
    tool_calls_seen = False
    
    async for event in result_stream.stream():
        if isinstance(event, ToolCallEvent):
            tool_calls_seen = True
            print(f"[Tool call: {event.tool_name}]")
        elif isinstance(event, TextEvent):
            print(event.text, end="", flush=True)
            
    # If we saw tool calls but no final text, explicitly request a summary
    if tool_calls_seen and not final_text_seen:
        # Request summary...
```

## Recommendation

**Switch to non-delta streaming** (Solution #1) as the simplest first approach to test. This change preserves the streaming experience for users while potentially fixing the tool call response issue.

If this doesn't resolve the issue, consider either:

1. Using `run_sync()` for tool call scenarios, or
2. Implementing a more sophisticated event-based approach with explicit handling for tool calls

The most robust long-term solution would be to better understand all the event types in the PydanticAI streaming implementation and handle each appropriately, but this would require more significant code changes.
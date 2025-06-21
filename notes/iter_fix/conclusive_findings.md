# Conclusive Findings on PydanticAI Stream Tool Call Issue

## Problem Summary

After thorough investigation of the PydanticAI codebase, I've confirmed the exact mechanism causing the issue with Claude 3 Haiku not providing final responses after tool calls when using `run_stream()`. This is **not a bug**, but rather a design limitation in how PydanticAI handles streaming.

## Root Cause: Early Termination on Tool Calls

The issue occurs because PydanticAI's streaming implementation is designed to terminate as soon as it detects something that could serve as a final result:

1. In `agent.py`, the `run_stream()` method uses a helper function called `stream_to_final()` that inspects the stream events coming from the model.

2. As soon as this function sees a `ToolCallPart` that matches the output schema, it returns a `FinalResult` object:

   ```python
   # Inside stream_to_final() function
   if isinstance(new_part, _messages.ToolCallPart) and output_schema:
       for call, _ in output_schema.find_tool([new_part]):
           return FinalResult(s, call.tool_name, call.tool_call_id)
   ```

3. Upon receiving this `FinalResult`, `run_stream()` immediately breaks out of its main processing loop:

   ```python
   # Inside run_stream()
   final_result_details = await stream_to_final(streamed_response)
   if final_result_details is not None:
       # ... setup StreamedRunResult ...
       yield StreamedRunResult(...)
       break  # <-- Stops processing the stream!
   ```

4. This means that after detecting a tool call, PydanticAI stops receiving any further stream events from the model, including any explanations or summaries it might generate after seeing the tool results.

## Why `run()` and `run_sync()` Work Better

`run()` and `run_sync()` work differently from `run_stream()` - they don't use the early-exit streaming approach. Instead, they complete the entire request/response cycle, allowing the model to provide a final response after tool calls.

## Why This Affects Claude Models More

Claude models (like Claude 3 Haiku) have a tendency to make tool calls and then provide explanatory text after the tool result is returned. OpenAI models might be more likely to embed tool calls within an overall text explanation, making them less affected by this issue.

## It's Not About Delta Streaming

Importantly, this issue affects both delta streaming (`delta=True`) and regular streaming (`delta=False`). The problem isn't about how the text deltas are processed but about the premature termination of stream processing when a tool call is detected.

## Solutions

### 1. Use Non-Streaming Methods

The most reliable solution is to use `run_sync()` instead of `run_stream()`:

```python
result = agent.run_sync(user_input, message_history=filtered_messages)
print(result.output)
```

This trades off the streaming experience for reliable tool call handling.

### 2. Use the Low-Level `iter()` Method

For more control, use the `iter()` method and implement your own stream processing logic:

```python
async with agent.iter(user_input, message_history=filtered_messages) as agent_run:
    async for node in agent_run:
        # Process each node type appropriately
        # ...
```

### 3. Request Explicit Summaries

After detecting a tool call and seeing no final explanation, make a follow-up request:

```python
# After processing a tool call with run_stream()
follow_up = agent.run_sync("Summarize what you found using the tool.", message_history=result_stream.all_messages())
print(follow_up.output)
```

## Recommendation

The simplest and most reliable solution is to use `run_sync()` instead of `run_stream()` for interactions that involve tool calls. This ensures you'll always get a complete response, including any explanations after tool calls are processed.

If streaming is essential, consider implementing a custom solution using the lower-level `iter()` method, which gives you more control over the execution flow.
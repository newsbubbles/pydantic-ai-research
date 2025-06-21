# PydanticAI Streaming Tool Call Issue Analysis

## Problem Summary

When using Claude 3 Haiku with PydanticAI in streaming mode, the model makes tool calls but does not produce a final response after receiving the tool result. This issue specifically occurs with `run_stream()` regardless of whether delta streaming (`delta=True`) or non-delta streaming is used.

## Code Analysis

### Streaming Implementation in PydanticAI

After examining the PydanticAI code, specifically `result.py` and `agent.py`, I've identified several key aspects of how streaming works:

1. **Streaming Flow Control**:
   - When calling `run_stream()`, the agent iterates through nodes in its graph until it finds a `ModelRequestNode`.  
   - For this node, it calls `_stream()` to get a streamed response from the model.  
   - The function `stream_to_final()` watches the stream for evidence of a final result.

2. **Final Result Detection**:
   ```python
   async def stream_to_final(s: models.StreamedResponse) -> FinalResult[models.StreamedResponse] | None:
       output_schema = graph_ctx.deps.output_schema
       async for maybe_part_event in streamed_response:
           if isinstance(maybe_part_event, _messages.PartStartEvent):
               new_part = maybe_part_event.part
               if isinstance(new_part, _messages.TextPart):
                   if _output.allow_text_output(output_schema):
                       return FinalResult(s, None, None)
               elif isinstance(new_part, _messages.ToolCallPart) and output_schema:
                   for call, _ in output_schema.find_tool([new_part]):
                       return FinalResult(s, call.tool_name, call.tool_call_id)
       return None
   ```

3. **Early Exiting on Tool Call**:
   - The code is designed to exit streaming when it sees a tool call part or a text part that matches the output schema.
   - **Critical point**: It immediately `break`s the loop after this, stopping the consumption of further stream events.

   ```python
   if (final_result_event := _get_final_result_event(event)) is not None:
       self._final_result_event = final_result_event
       yield final_result_event
       break
   ```

4. **Run Completion**:
   - After breaking the loop, the code calls `on_complete()` which processes the tool calls, but it doesn't have explicit handling for generating a final response if needed.

## The Root Cause

The issue occurs because:

1. The streaming implementation is designed to exit early when it detects a tool call.
2. It doesn't have built-in handling to wait for or generate a final text response after the tool call is processed.
3. The code assumes that the final output would either be a tool call result OR a text result, but not a sequence of tool call followed by text.

This behavior affects both delta and non-delta streaming modes, since the issue is with the fundamental design of the streaming flow control logic.

## Model-Specific Differences

Different models handle tool calls in different ways:

- **Claude models** (like Claude 3 Haiku) seem to be more sensitive to this issue, often stopping after making a tool call.
- **OpenAI models** may be more likely to continue and produce a text response after a tool call is processed, though this is not guaranteed.

This explains why the issue might appear more frequently with Claude 3 Haiku.

## Possible Solutions

### 1. Use `run()` or `run_sync()` Instead of `run_stream()`

The non-streaming methods handle the complete cycle of request/response/tool-execution and are more likely to result in a proper final text response after tool calls.

```python
result = agent.run_sync(user_input, message_history=filtered_messages)
print(result.output)
```

### 2. Modify the Agent's Prompt

Explicitly instruct the model to always provide a summary after tool calls:

```python
prompt = f"""
# Filesystem Agent

You are a helpful assistant that specializes in working with the filesystem.

# IMPORTANT: After calling any tool, always provide a short summary of what you found or did.
# Never stop after just making a tool call - always provide text output after the tool returns.
...
"""
```

### 3. Add a Follow-up Request After Tool Calls

If the response appears to be tool-calls only, make an explicit follow-up request:

```python
if tool_call_detected and not text_response:
    follow_up = agent.run_sync("Summarize what you just found using the tool.", message_history=result_stream.all_messages())
    print(follow_up.output)
```

### 4. Use the Lower-Level `iter()` Method 

For more control, use the `iter()` method and manually handle tool calls and responses:

```python
async with agent.iter(user_input, message_history=filtered_messages) as agent_run:
    async for node in agent_run:
        # Handle each node type differently
        if agent.is_call_tools_node(node):
            # Extract and display tool call result
            tool_result = extract_result(node)
            print(f"Tool result: {tool_result}")
            
        # Handle final result when we reach the end
        if agent.is_end_node(node):
            print(f"Final answer: {agent_run.result.output}")
```

## Recommendation

**Use `run_sync()` Instead of `run_stream()`** as the most straightforward solution.

If streaming is essential, consider modifying your agent script to switch to the `iter()` method with custom handling for tool calls and responses. This approach gives you more control over the execution flow, allowing you to properly handle the tool call/response cycle and ensure you always get a final text response.

```python
async with agent.iter(user_input, message_history=filtered_messages) as agent_run:
    # Custom streaming implementation
    # ...
```

Long-term, this appears to be a design limitation in PydanticAI's streaming implementation that would need to be addressed in a future version of the library.
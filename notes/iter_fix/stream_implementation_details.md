# PydanticAI Streaming Implementation Details

After carefully examining the PydanticAI code, I've identified the specific mechanism behind the streaming tool call issues with Claude models.

## How `run_stream()` Works

The `run_stream()` method in `agent.py` follows this flow:

1. It iterates through nodes in the agent's execution graph.

2. When it encounters a `ModelRequestNode`, it creates a streamed response by calling `node._stream(graph_ctx)`.

3. It then uses a critical function called `stream_to_final()` that watches the stream for evidence that would indicate a final result:

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

**The key issue is here:** As soon as the function sees a `ToolCallPart` that matches the output schema, it returns a `FinalResult` and the streaming process **immediately breaks out** of the main loop:

```python
final_result_details = await stream_to_final(streamed_response)
if final_result_details is not None:
    # ... setup StreamedRunResult ...
    yield StreamedRunResult(...)
    break  # <-- Stops processing the stream!
```

## Why This Causes Problems

This design has several important implications:

1. **Early Exit:** The streaming implementation is designed to exit as soon as it sees something that could be a final result (either a tool call or text content).

2. **No Continuation:** There's no mechanism to continue receiving stream events after a tool call is processed. The function simply yields a `StreamedRunResult` and breaks.

3. **Tool Call vs. Final Response:** The implementation assumes that either your final output is a tool call OR text content, but not a sequence of tool call followed by explanatory text.

## Why Claude Models are More Affected

Different LLM models handle tool calls differently:

1. **Claude Models** (like Claude 3 Haiku) are designed to follow a pattern where they'll frequently make a tool call, wait for the result, and then provide a final explanatory text response.

2. **OpenAI Models** might be more likely to make tool calls and wrap them in an overall text explanation, making them less affected by this issue.

The problem appears more frequently with Claude because of its tendency to strictly separate the tool call from the explanatory text afterward.

## How `stream_text()` Fits In

When we look at the `stream_text()` function in `result.py`, we can see that whether delta mode is true or false doesn't change the fundamental issue:

```python
async def stream_text(self, *, delta: bool = False, debounce_by: float | None = 0.1) -> AsyncIterator[str]:
    # ... code ...
    if delta:
        async for text in self._stream_text_deltas():
            yield text
    else:
        # ... builds up full text ...
        async for text in self._stream_text_deltas():
            deltas.append(text)
            yield ''.join(deltas)
    # ... mark as completed ...
```

Regardless of delta mode, the stream processing has already stopped as soon as the tool call was detected, meaning there's nothing more to stream after the tool call is processed.

## Example of What's Happening

1. User submits: "list the files in the current directory"

2. The Claude model begins its response stream by making a tool call to the `list_files` function

3. `stream_to_final()` sees the tool call, immediately returns it as the final result

4. `run_stream()` breaks out of its loop, yielding a `StreamedRunResult`

5. This result doesn't contain any text response from the model - just the tool call

6. The tool gets executed (successfully), but because we've already broken out of processing the stream, we never see any final explanatory text from Claude about the results

## Conclusion: It's a Design Limitation

This is a fundamental design decision in PydanticAI's streaming implementation. The library considers a tool call to be an endpoint in itself, without expecting a follow-up text explanation.

For models like Claude that want to provide explanatory text after a tool call and result, the streaming implementation prematurely terminates this process before the explanatory text can be generated.

This explains why the non-streaming `run()` and `run_sync()` methods work better - they don't terminate early on seeing a tool call; they complete the entire request/response cycle.
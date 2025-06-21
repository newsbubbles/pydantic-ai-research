# StreamedRunResult Output Error

## Issue Description

When running the agent with streaming enabled, we encountered the following error:

```
AttributeError: 'StreamedRunResult' object has no attribute 'output'
```

This occurs in `agent_test.py` when trying to access `result.output` after using `stream_text(delta=True)` for streaming the model response.

## Root Cause Analysis

After investigating the Pydantic-AI documentation and related GitHub issues, we identified that when using `StreamedRunResult.stream_text(delta=True)`, the library never constructs a complete output string. According to the documentation:

> The final result message will NOT be added to result messages if you use `.stream_text(delta=True)` since in this case the result content is never built as one string.

When using `delta=True`, each chunk is streamed individually for maximum efficiency, but this means the complete output is never consolidated into the `output` attribute of the `StreamedRunResult` object.

## Solution

There are three potential solutions to this issue:

1. **Use `stream_text()` without `delta=True`** - This will stream the full text up to the current point and will properly populate the `output` attribute, but lacks the efficiency of delta streaming.

2. **Capture the complete output manually** - We can modify our code to concatenate the delta chunks ourselves and store the complete output in a variable.

3. **Use `get_output()` method** - After streaming is complete, call the `get_output()` method which properly builds and returns the full output (as documented in the Pydantic-AI API reference).

## Implementation

We'll implement solution #2 since it preserves the efficiency of delta streaming while addressing our needs:

```python
# Original problematic code
async with agent.run_stream(user_input, message_history=message_history) as result_stream:
    # Use delta streaming to show output as it's generated
    async for delta in result_stream.stream_text(delta=True):
        print(delta, end="", flush=True)
    
    # Get the full response and update message history
    result = result_stream
    # This line causes the error because result.output doesn't exist
    logger.info(f"Complete response received, length: {len(result.output) if result.output else 0}")
    
    message_history.append({"role": "user", "content": user_input})
    message_history.append({"role": "assistant", "content": result.output})
```

```python
# Fixed code that manually tracks the complete response
async with agent.run_stream(user_input, message_history=message_history) as result_stream:
    # Initialize a variable to accumulate the complete response
    complete_response = ""
    
    # Use delta streaming to show output as it's generated
    async for delta in result_stream.stream_text(delta=True):
        print(delta, end="", flush=True)
        complete_response += delta
    
    # Get the full response and update message history
    result = result_stream
    logger.info(f"Complete response received, length: {len(complete_response)}")
    
    message_history.append({"role": "user", "content": user_input})
    message_history.append({"role": "assistant", "content": complete_response})
```

This solution maintains the efficiency and immediacy of delta streaming while ensuring we properly track the complete output for message history.

## Related Documentation

- [Pydantic-AI Message History](https://ai.pydantic.dev/message-history/)
- [Pydantic-AI StreamedRunResult API](https://ai.pydantic.dev/api/result/)

## Similar Issues

This issue is related to but distinct from other Pydantic-AI streaming issues such as:

- [Azure OpenAI API Streaming Response Causes AttributeError](https://github.com/pydantic/pydantic-ai/issues/797) - About missing content fields in delta chunks
- [Streaming Tool Calls](https://github.com/pydantic/pydantic-ai/issues/640) - About showing tool calls during streaming
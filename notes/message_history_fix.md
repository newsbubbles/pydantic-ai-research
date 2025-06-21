# Pydantic AI Message History Issue & Fix

## Problem Overview

The original implementation in `agent_test.py` was using a naive approach to message history management, storing messages as simple dictionaries:

```python
message_history.append({"role": "user", "content": user_input})
message_history.append({"role": "assistant", "content": complete_response})
```

This resulted in an assertion error:

```
AssertionError: Expected code to be unreachable, but got: {'role': 'user', 'content': 'list the current folder contents'}
```

The error occurred in the OpenAI model implementation, specifically during message mapping in `pydantic_ai/models/openai.py` in the `_map_messages` method, which uses `assert_never(message)` when it encounters an unsupported message format.

## Key Research Findings

1. **Correct Message Format**: Pydantic AI uses a specific structured format for messages based on the `ModelMessage` hierarchy with strongly typed parts like `SystemPromptPart`, `UserPromptPart`, etc.

2. **History Processing**: Instead of manually appending to the history, we should use the agent's result methods like `all_messages()` or `new_messages()` to get properly formatted messages.

3. **Filtering Requirements**: When maintaining history across turns, we need to consider:
   - Tool call/return pairs that should be kept together
   - System messages that should always be preserved
   - Token limits that might require trimming older messages

## Solution Implementation

We implemented a proper `filtered_message_history` function based on the approach used in the `tooler` project:

```python
def filtered_message_history(
    result: Optional[AgentRunResult], 
    limit: Optional[int] = None, 
    include_tool_messages: bool = True
) -> Optional[List[ModelMessage]]:
    # ...
```

This function:

1. Extracts all messages using `result.all_messages()`
2. Identifies and preserves system messages
3. Applies filtering based on parameter settings
4. Maintains tool call/return pairs
5. Applies message limits while preserving context

## Changes to Log File Handling

We also improved the logging setup to ensure logs are properly saved to the `logs` directory:

1. Created a `logs` directory in the project root
2. Updated logging configuration to save to `logs/debug.log`
3. Passed the log directory to the MCP server via environment variables
4. Ensured consistent logging format across components

## Testing & Verification

The fixed version has been tested and successfully handles message history properly. The agent can now maintain context across turns without encountering the assertion error.

## References

- [Pydantic AI Message History Documentation](https://ai.pydantic.dev/message-history/)
- [Pydantic AI Messages API](https://ai.pydantic.dev/api/messages/)
- Example of proper implementation in the `tooler` project

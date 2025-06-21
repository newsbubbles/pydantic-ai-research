# Pydantic AI Research Project

This project contains research tests and experiments with the Pydantic AI framework, particularly focusing on message history management and MCP servers.

## Key Components

- `src/agent_test.py`: Original agent test with message history issues
- `src/agent_test_fixed.py`: Fixed version with proper message history implementation
- `src/mcp_servers/filesystem_mcp.py`: MCP server implementing filesystem operations

## Issue Resolution

### Issue: AssertionError in Message History

When running the filesystem agent, we encountered an error in handling message history:

```
AssertionError: Expected code to be unreachable, but got: {'role': 'user', 'content': 'list the current folder contents'}
```

This error occurred because the original `agent_test.py` was using a simple dict format for message history, while Pydantic AI expects a proper `ModelMessage` type hierarchy.

### Solution

Implemented a `filtered_message_history` function in `agent_test_fixed.py` that:

1. Uses the proper `ModelMessage` objects from the result
2. Intelligently filters the history to include relevant messages
3. Maintains tool call/return pairs as needed
4. Limits the history size to prevent excessive tokens

## Running the Agent

To run the fixed agent:

```bash
python src/agent_test_fixed.py
```

The logs are stored in the `logs/` directory, including:

- `logs/debug.log` - Main agent logs
- `logs/filesystem_mcp.log` - MCP server logs

## Environment Variables

- `OPENROUTER_API_KEY` - API key for OpenRouter (preferred)
- `OPENAI_API_KEY` - API key for OpenAI (fallback)

One of these must be set for the agent to run properly.
# pydantic-ai-research

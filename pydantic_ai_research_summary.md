# PydanticAI Research Summary

## Overview

PydanticAI is a Python agent framework designed to make building production-grade applications with Generative AI more intuitive and type-safe. It was created by the team behind Pydantic, bringing a similar developer experience to GenAI applications that FastAPI brought to web development.

In the XSUS project, PydanticAI forms the foundation of the agent system, particularly for the Tooler agent which builds custom API clients based on user requirements.

## Key Components Researched

1. **Agent Architecture**: The core abstraction for interacting with LLMs, managing tools, and handling responses
2. **MCP (Model Context Protocol)**: Standardized protocol for communication between AI applications
3. **Streaming**: Real-time streaming of model responses to clients
4. **Models and Providers**: Abstraction for different LLM providers and models
5. **Testing Approaches**: Strategies for testing agent behavior

## Critical Findings

### Agent Architecture

- Agents are initialized with models, MCP servers, and system prompts
- The XSUS project caches agent instances for performance using a custom agent manager
- System prompts define the agent's behavior and are loaded from markdown files

### MCP Implementation

- MCP servers extend agent functionality through standardized tool interfaces
- Servers receive requests and return responses through stdin/stdout
- The XSUS project uses two main MCP servers for project tools and web search/scraping
- Proper environment variable management is critical for MCP servers

### Streaming Implementation

- PydanticAI supports delta and full-text streaming modes
- Streaming is implemented in XSUS using FastAPI's StreamingResponse and WebSockets
- Common issues include connection management, message history, and error handling
- Proper context manager usage is essential for resource cleanup

### Model Configuration

- XSUS primarily uses Anthropic Claude models through OpenRouter
- The OpenAI provider is used with the OpenRouter base URL for compatibility
- Fallback to direct OpenAI models is implemented for reliability

### Testing Approaches

- Agent testing involves standalone scripts for interactive testing
- End-to-end testing with predefined prompts in JSON files
- Error handling and retry mechanisms are important for test reliability

## Common Issues and Solutions

### Connection Management

**Issue**: Resources not properly cleaned up after streaming or errors

**Solution**: Always use proper context managers
```python
async with agent.run_mcp_servers():
    async with agent.run_stream(user_input) as result:
        # Process streaming result
```

### Message History Management

**Issue**: Final messages not added to history when using delta streaming

**Solution**: Manually append messages for delta streaming
```python
full_response = ""
async for delta in result.stream_text(delta=True):
    full_response += delta
    # Process delta

# Manually add to history
message_history.append({"role": "user", "content": user_input})
message_history.append({"role": "assistant", "content": full_response})
```

### Error Handling in Streaming

**Issue**: Errors during streaming can break client connections

**Solution**: Implement retry logic and graceful error responses
```python
async def stream_with_retries(max_retries=3):
    for attempt in range(max_retries):
        try:
            async with agent.run_stream(user_input) as result:
                async for delta in result.stream_text(delta=True):
                    yield delta
                break  # Success
        except Exception as e:
            if attempt == max_retries - 1:
                yield f"Error: {str(e)}"
```

### MCP Server Environment

**Issue**: Environment variables not properly passed to MCP servers

**Solution**: Explicitly set environment variables when creating servers
```python
env = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
    "SERPER_API_KEY": os.getenv("SERPER_API_KEY"),
    "ROOT_FOLDER": "./data/projects"
}

mcp_servers = [MCPServerStdio('python', [server_path], env=env)]
```

## Integration in XSUS

The XSUS project integrates PydanticAI through several key components:

1. **Agent Creation**: `backend/app/agents/tooler_agent.py` sets up the Tooler agent with appropriate models and MCP servers

2. **Agent Management**: `backend/app/core/agent_manager.py` handles caching and lifecycle management of agent instances

3. **Chat Interface**: `backend/app/api/chat_streaming.py` implements streaming of agent responses to clients

4. **Database Storage**: Chat sessions and messages are stored in the database for persistence

This integration creates a robust system for building and interacting with custom API clients through a chat interface.

## Recommendations for XSUS

1. **Error Monitoring**: Implement comprehensive monitoring of streaming errors

2. **Connection Pooling**: Consider implementing connection pooling for improved performance

3. **Message History Optimization**: Optimize message history management to prevent context loss

4. **Test Coverage**: Expand the suite of test prompts for automated testing

5. **Resource Management**: Ensure proper cleanup of all resources, especially during application shutdown

## Resources

- Official Documentation: [ai.pydantic.dev](https://ai.pydantic.dev/)
- GitHub Repository: [github.com/pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai)
- Cheatsheets: See `pydantic_ai_streaming_cheatsheet.md` and `pydantic_ai_mcp_server_cheatsheet.md`
- Research Notes: See the `notes` folder for detailed notes on specific topics
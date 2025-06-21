# PydanticAI Research Index

This document serves as an index to the research notes on PydanticAI in the context of the XSUS project.

## Overview and Core Concepts

- [01_overview.md](01_overview.md): Introduction to PydanticAI and its key features
- [02_models_and_providers.md](02_models_and_providers.md): Overview of model architecture and provider options

## Agents

- [01_agent_basics.md](../agents/01_agent_basics.md): Basics of PydanticAI agents and their implementation in XSUS

## MCP (Model Context Protocol)

- [01_mcp_overview.md](../mcp_servers/01_mcp_overview.md): Overview of the Model Context Protocol
- [02_mcp_implementation.md](../mcp_servers/02_mcp_implementation.md): Detailed implementation of MCP servers

## Streaming

- [01_streaming_basics.md](../streaming/01_streaming_basics.md): Fundamentals of streaming in PydanticAI
- [02_streaming_issues.md](../streaming/02_streaming_issues.md): Common issues and solutions for streaming

## Examples and Testing

- [01_chat_app.md](../examples/01_chat_app.md): Chat application example with FastAPI
- [02_testing_agents.md](../examples/02_testing_agents.md): Approaches for testing agents

## Key Summary Points

1. **Framework Overview**: PydanticAI is a Python framework for building production-grade AI applications with a focus on type safety, structured responses, and dependency injection.

2. **Integration in XSUS**: In the XSUS project, PydanticAI is used primarily for the Tooler agent, which builds custom API clients based on user requirements.

3. **Agent Architecture**: Agents in PydanticAI are configured with models, MCP servers, and system prompts. In XSUS, the agent management system maintains a cache of agent instances.

4. **MCP Implementation**: MCP servers in XSUS extend agent functionality, particularly for file management and web searching/scraping.

5. **Streaming**: Streaming is a critical feature for the chat interface in XSUS, with various challenges around connection management, error handling, and message history.

6. **Testing Approaches**: Testing agent behavior involves unit tests, integration tests, and end-to-end tests with predefined prompts.

7. **Model Configuration**: XSUS primarily uses Anthropic Claude models via OpenRouter, with OpenAI as a fallback.

## Critical Considerations

1. **Connection Management**: Ensuring proper setup and teardown of streaming connections and MCP servers

2. **Error Handling**: Robust error handling throughout the system, particularly during streaming

3. **Message History**: Careful management of message history to maintain context without exceeding limits

4. **Environment Variables**: Proper configuration of environment variables for API keys and other settings

5. **Tool Implementation**: Careful implementation of tools in MCP servers to ensure reliability and security
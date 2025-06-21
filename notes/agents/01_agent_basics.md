# PydanticAI Agents

## Agent Basics

In PydanticAI, an Agent is the primary interface for interacting with LLMs. It manages the flow of messages, tool execution, and structured responses.

## Agent Creation

A basic Agent can be created as follows:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Create a model instance
model = OpenAIModel("gpt-4o")

# Create an agent with a system prompt
agent = Agent(model, system_prompt="You are a helpful assistant.")

# Run the agent
result = await agent.run("Hello, how are you today?")
print(result.output)
```

## Agent in XSUS Project

In the XSUS project, agents are used in several ways:

1. **Tooler Agent**: A specialized agent for building custom API clients. The implementation is in `backend/app/agents/tooler_agent.py`.

2. **System Integration**: Agents are integrated into the system through the `backend/app/core/agent_manager.py` which maintains a cache of agent instances.

3. **Chat Interface**: Agents handle user requests through a chat interface, with responses streamed back to the client.

## Agent Components in XSUS

### MCP Servers

The agent in XSUS is configured with MCP servers for extending functionality:

```python
mcp_servers = [
    # Project Tools MCP for working with files, variables, etc.
    MCPServerStdio('python', [project_tools_file], env=env),
    # Search and Scraping MCP for web searching and scraping
    MCPServerStdio('python', [serper_scrape_file], env=env),
]
```

### Model Configuration

The XSUS project primarily uses Anthropic's Claude models via OpenRouter:

```python
model = OpenAIModel(
    'anthropic/claude-3.7-sonnet',
    provider=OpenAIProvider(
        base_url='https://openrouter.ai/api/v1',
        api_key=OPENROUTER_API_KEY
    )
)
```

## Agent Lifecycle

1. **Initialization**: Agent is created with a model and optional MCP servers
2. **System Prompt**: The agent is configured with a system prompt defining its behavior
3. **Running**: The agent processes user messages, calling tools as needed
4. **Message Management**: The agent maintains chat history for context
5. **Cleanup**: Resources are cleaned up when the agent is no longer needed

In the XSUS project, this lifecycle is managed by the `agent_manager.py` module, which handles caching of agent instances and proper cleanup.
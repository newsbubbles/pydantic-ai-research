# Model Context Protocol (MCP) in PydanticAI

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol that allows AI applications to connect to external tools and services using a common interface. It enables different AI systems to communicate with each other without needing specific integrations for each service.

## MCP in PydanticAI

PydanticAI supports MCP in three ways:

1. **Client**: Agents act as MCP clients, connecting to MCP servers to use their tools
2. **Server**: Agents can be used within MCP servers
3. **Server Development**: PydanticAI includes tools for building MCP servers

## MCP Client Usage in XSUS

In the XSUS project, the Tooler agent is set up as an MCP client that connects to two MCP servers:

```python
# Setup environment variables for MCP servers
env = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
    "SERPER_API_KEY": SERPER_API_KEY,
    "ROOT_FOLDER": "./data/projects"
}

# Setup MCP Servers
mcp_servers = [
    # Project Tools MCP for working with files, variables, etc.
    MCPServerStdio('python', [project_tools_file], env=env),
    # Search and Scraping MCP for web searching and scraping
    MCPServerStdio('python', [serper_scrape_file], env=env),
]

# Create and return the agent
agent = Agent(model, mcp_servers=mcp_servers, system_prompt=agent_prompt)
```

The `MCPServerStdio` class is used to create MCP server instances that communicate with the agent via standard input/output.

## MCP Server Implementation

MCP servers in PydanticAI implement a standardized protocol for tool registration and execution. When a server is initialized, it registers a set of tools that the client (agent) can use.

Here's a basic structure of an MCP server:

```python
import json
import sys

def handle_request(request):
    """Handle incoming MCP requests"""
    method = request.get("method")
    
    if method == "initialize":
        # Return capabilities and tool specs
        return {
            "schema_version": "v1",
            "capabilities": ["function_calling"],
            "tool_specs": get_tool_specs()
        }
        
    elif method == "execute_function":
        # Execute the requested function and return result
        function_name = request.get("function_name")
        params = request.get("parameters", {})
        
        if function_name == "search":
            return {"result": search(**params)}
        # Handle other functions...

def main():
    """Main MCP server loop"""
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

# Run the server
if __name__ == "__main__":
    main()
```

## MCP in the XSUS Architecture

In XSUS, MCP plays a central role in the architecture:

1. **Tool Organization**: MCP servers encapsulate related functionality (file handling, web searching)
2. **Agent Extension**: The Tooler agent is extended with capabilities from MCP servers
3. **Service Architecture**: MCP servers provide a service-oriented approach to agent capabilities

The infrastructure for managing MCP servers is primarily handled in `backend/app/agents/tooler_agent.py` which sets up the servers, and `backend/app/core/agent_manager.py` which manages their lifecycle.
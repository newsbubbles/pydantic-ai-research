# PydanticAI MCP Server Cheatsheet

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol allowing AI applications to communicate with external tools and services.

## Basic MCP Server Structure

```python
#!/usr/bin/env python3
import json
import sys
import logging
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, filename="mcp_server.log")
logger = logging.getLogger("mcp_server")

# Tool implementations
def my_tool(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """Example tool documentation"""
    # Implementation
    return {"result": f"Processed {param1} with {param2}"}

# Tool specifications
def get_tool_specs() -> List[Dict[str, Any]]:
    return [
        {
            "name": "my_tool",
            "description": "Example tool documentation",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "First parameter"},
                    "param2": {"type": "integer", "description": "Second parameter"}
                },
                "required": ["param1"]
            }
        }
    ]

# Request handling
def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    method = request.get("method")
    
    if method == "initialize":
        return {
            "schema_version": "v1",
            "capabilities": ["function_calling"],
            "tool_specs": get_tool_specs()
        }
    
    elif method == "execute_function":
        function_name = request.get("function_name")
        params = request.get("parameters", {})
        
        if function_name == "my_tool":
            try:
                result = my_tool(**params)
                return {"result": result}
            except Exception as e:
                return {"error": str(e)}
        else:
            return {"error": f"Unknown function: {function_name}"}
    else:
        return {"error": f"Unknown method: {method}"}

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

## Connecting MCP Server to an Agent

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel

# Setup environment variables
env = {
    "API_KEY": "your-api-key",
    "OTHER_CONFIG": "value"
}

# Create model
model = OpenAIModel("gpt-4o")

# Create MCP server
mcp_server = MCPServerStdio('python', ['mcp_server.py'], env=env)

# Create agent with MCP server
agent = Agent(model, mcp_servers=[mcp_server], system_prompt="You are a helpful assistant.")

# Run the agent with MCP server
async def run_agent():
    async with agent.run_mcp_servers():
        result = await agent.run("Use my_tool with param1='test'")
        print(result.output)
```

## Advanced Tool Implementation

```python
# Complex tool with structured input/output
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str

def search_web(query: str, num_results: int = 5) -> List[SearchResult]:
    """Search the web for information"""
    # Implementation would use an actual search API
    results = []
    for i in range(min(3, num_results)):
        results.append(SearchResult(
            title=f"Result {i+1} for {query}",
            url=f"https://example.com/result{i+1}",
            snippet=f"This is a snippet for result {i+1} related to {query}."
        ))
    return results

# Convert to JSON-serializable format
def search_web_wrapper(query: str, num_results: int = 5) -> Dict[str, Any]:
    results = search_web(query, num_results)
    return {
        "results": [
            {"title": r.title, "url": r.url, "snippet": r.snippet}
            for r in results
        ]
    }
```

## Tool Specification Patterns

```python
def get_detailed_tool_specs():
    return [
        {
            "name": "search_web",
            "description": "Search the web for information.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5).",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "weather",
            "description": "Get weather information for a location.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location."
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius",
                        "description": "Temperature units."
                    }
                },
                "required": ["location"]
            }
        }
    ]
```

## Error Handling in MCP Servers

```python
def execute_tool(function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool and handle errors"""
    try:
        if function_name == "search_web":
            return {"result": search_web_wrapper(**params)}
        elif function_name == "weather":
            return {"result": get_weather(**params)}
        else:
            return {
                "error": {
                    "type": "unknown_function",
                    "message": f"Function '{function_name}' not found"
                }
            }
    except KeyError as e:
        return {
            "error": {
                "type": "missing_parameter",
                "message": f"Missing required parameter: {str(e)}"
            }
        }
    except ValueError as e:
        return {
            "error": {
                "type": "invalid_parameter",
                "message": str(e)
            }
        }
    except Exception as e:
        return {
            "error": {
                "type": "execution_error",
                "message": str(e)
            }
        }
```

## Using Environment Variables

```python
import os

def get_api_config():
    """Get configuration from environment variables"""
    return {
        "api_key": os.environ.get("API_KEY"),
        "api_url": os.environ.get("API_URL", "https://api.default.com"),
        "timeout": int(os.environ.get("TIMEOUT", "30")),
        "max_results": int(os.environ.get("MAX_RESULTS", "10"))
    }

# Use in tools
def api_call_tool(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    config = get_api_config()
    # Use config values for API calls
    return {"result": "API call result"}
```

## Debugging MCP Servers

```python
def setup_logging():
    """Set up detailed logging for debugging"""
    log_dir = os.environ.get("LOG_DIR", ".")
    log_file = os.path.join(log_dir, "mcp_server.log")
    
    logger = logging.getLogger("mcp_server")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

## Common Issues and Solutions

1. **JSON Serialization**: Always ensure objects are JSON-serializable before returning

2. **Environment Variables**: Include fallbacks for missing environment variables

3. **Process Management**: Ensure proper stdin/stdout handling with flush() calls

4. **Error Propagation**: Return structured errors for better client handling

5. **Logging**: Use detailed logging for troubleshooting

6. **Timeouts**: Implement timeouts for external API calls

7. **Resource Cleanup**: Properly close connections and resources
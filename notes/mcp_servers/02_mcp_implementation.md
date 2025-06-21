# MCP Server Implementation in PydanticAI

## MCP Server Structure

An MCP server in PydanticAI consists of several key components:

1. **Initialization Handler**: Responds to the `initialize` method call from clients
2. **Tool Specifications**: Defines the tools available to clients
3. **Tool Execution**: Handles execution of tool functions when called
4. **I/O Management**: Handles communication with clients via stdin/stdout

## Sample MCP Server Implementation

Here's a more detailed example of an MCP server implementation:

```python
#!/usr/bin/env python3
import json
import sys
import logging
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("mcp_server.log"), logging.StreamHandler()]
)
logger = logging.getLogger("mcp_server")

# Tool implementations
def search_web(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Search the web for information"""
    logger.info(f"Searching for: {query} (results: {num_results})")
    # Implementation would go here
    return [
        {"title": "Example result", "url": "https://example.com", "snippet": "This is an example search result"}
    ]

def scrape_url(url: str) -> Dict[str, Any]:
    """Scrape content from a URL"""
    logger.info(f"Scraping URL: {url}")
    # Implementation would go here
    return {"title": "Example Page", "content": "This is example content from the page"}

# Tool specifications
def get_tool_specs() -> List[Dict[str, Any]]:
    """Get specifications for all available tools"""
    return [
        {
            "name": "search_web",
            "description": "Search the web for information",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "num_results": {"type": "integer", "description": "Number of results to return"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "scrape_url",
            "description": "Scrape content from a URL",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to scrape"}
                },
                "required": ["url"]
            }
        }
    ]

# Request handling
def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming MCP requests"""
    method = request.get("method")
    logger.info(f"Received request with method: {method}")
    
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
        
        logger.info(f"Executing function: {function_name} with params: {params}")
        
        try:
            if function_name == "search_web":
                result = search_web(**params)
                return {"result": result}
            elif function_name == "scrape_url":
                result = scrape_url(**params)
                return {"result": result}
            else:
                return {"error": f"Unknown function: {function_name}"}
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {str(e)}")
            return {"error": str(e)}
    else:
        return {"error": f"Unknown method: {method}"}

def main():
    """Main MCP server loop"""
    logger.info("MCP Server starting")
    
    while True:
        line = sys.stdin.readline()
        if not line:
            logger.info("End of input, shutting down")
            break
        
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {str(e)} | Input: {line}")
            print(json.dumps({"error": f"Invalid JSON: {str(e)}"}))  
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            print(json.dumps({"error": f"Server error: {str(e)}"}))  
            sys.stdout.flush()

# Run the server
if __name__ == "__main__":
    main()
```

## MCP Server in XSUS

In the XSUS project, MCP servers are used to extend the functionality of the Tooler agent. The main servers include:

1. **Project Tools MCP**: Provides tools for working with files, variables, etc.
2. **Search and Scraping MCP**: Provides tools for web searching and scraping

These servers are started as separate processes by the Agent when it runs.

## MCPServerStdio Class

The `MCPServerStdio` class in PydanticAI handles the communication with MCP servers:

```python
class MCPServerStdio:
    def __init__(self, program, args, env=None):
        """Initialize an MCP server that communicates via stdin/stdout
        
        Args:
            program: The program to run (e.g. 'python')
            args: Arguments to the program (e.g. ['server.py'])
            env: Environment variables to pass to the process
        """
        self.program = program
        self.args = args
        self.env = env or {}
        self.process = None
        
    async def start(self):
        """Start the MCP server process"""
        # Create merged environment
        full_env = os.environ.copy()
        full_env.update(self.env)
        
        # Start the process
        self.process = await asyncio.create_subprocess_exec(
            self.program,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=full_env
        )
        
    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception:
                pass
            self.process = None
            
    async def call(self, request):
        """Send a request to the MCP server and get the response"""
        if not self.process:
            await self.start()
            
        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode())
        
        return response
```

## Common MCP Server Issues

1. **Process Management**: Ensuring processes are properly started and stopped
2. **Environment Variables**: Managing environment variables needed by MCP servers
3. **Error Handling**: Dealing with errors in the server or communication
4. **Security**: Ensuring the server doesn't expose sensitive information

## MCP Server Testing

Testing MCP servers requires ensuring both the protocol handling and tool implementations work correctly:

```python
async def test_mcp_server():
    # Start the server
    server = MCPServerStdio('python', ['mcp_server.py'])
    try:
        # Initialize
        init_response = await server.call({"method": "initialize"})
        assert init_response.get("schema_version") == "v1"
        assert "function_calling" in init_response.get("capabilities", [])
        
        # Call a function
        func_response = await server.call({
            "method": "execute_function",
            "function_name": "search_web",
            "parameters": {"query": "test query"}
        })
        assert "result" in func_response
        assert isinstance(func_response["result"], list)
    finally:
        # Ensure the server is stopped
        await server.stop()
```
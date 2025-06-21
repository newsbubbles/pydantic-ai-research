# MCP Server Initialization Issues Analysis

## Date: 2025-06-20

## Problem Summary

The PydanticAI agent test script is failing during MCP server initialization. The agent attempts to connect to the MCP server, but the initialization times out after 30 seconds. The core issue appears to be a communication breakdown during the initial handshake between the agent (client) and the MCP server.

## Diagnostic Observations

### Log Analysis

1. **Client Logs**:
   - The agent tries to start the MCP servers with a 30-second timeout
   - It encounters `Timeout while starting MCP servers` error
   - Multiple asyncio-related errors occur during cleanup
   - Specific error: `asyncio.exceptions.CancelledError` during `client.initialize()`

2. **Server Logs**:
   - Server successfully starts up
   - Receives initialize request from client
   - Responds with tools specifications and capabilities
   - Waits for next request (which never comes)

3. **Protocol Mismatch**:
   - Client sends: `{"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"sampling":{},"roots":{"listChanged":true}},"clientInfo":{"name":"mcp","version":"0.1.0"}},"jsonrpc":"2.0","id":0}`
   - Server responds: `{"schema_version": "v1", "capabilities": ["function_calling"], "tool_specs": [...]}`
   - The server response is missing required JSON-RPC 2.0 fields: `jsonrpc`, `id`, and the response is not wrapped in a `result` object

## Research Findings

### MCP Protocol Requirements

According to the [MCP Lifecycle specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle), responses must follow JSON-RPC 2.0 format:

1. Client sends an `initialize` request with protocol version
2. Server must respond with a valid JSON-RPC response including the same `id` as the request
3. Client then sends an `initialized` notification

The server is not following this format, which causes the client to timeout waiting for a properly formatted response.

### Similar Issues

1. **Issue #308 - MCP Server Disconnected**:
   - Similar issues reported where MCP servers disconnect
   - Root cause identified as JSON formatting issues
   - Recommendation: "Make sure all your JSON-RPC messages go to stdout and end with a newline"
   - Proper JSON-RPC formatting is essential

2. **Issue #1675 - Remote MCP Server Not Working**:
   - Issues with PydanticAI MCP client connecting to SSE servers
   - Tool discovery problems similar to our situation

3. **Issue #1860 - Streaming Errors**:
   - Compatibility issues between PydanticAI versions and MCP server implementations
   - User had to downgrade PydanticAI to make it work

### Python Version Compatibility

No specific issues were found regarding Python 3.12 compatibility with MCP server implementations. The issue appears to be more related to the JSON-RPC protocol implementation rather than the Python version.

## Root Cause

The root cause appears to be a **JSON-RPC format mismatch** in the server response:

1. The MCP server is responding with a custom format (`schema_version`, `capabilities`, `tool_specs`) instead of the required JSON-RPC 2.0 format
2. The client is expecting a response with `jsonrpc: "2.0"`, `id: 0` and the content wrapped in a `result` object
3. Because of this mismatch, the client never receives what it considers a valid response and times out

## Recommended Solution

Modify the MCP server to properly format JSON-RPC 2.0 responses:

```python
# Current incorrect format:
{
    "schema_version": "v1", 
    "capabilities": ["function_calling"], 
    "tool_specs": [...]
}

# Required JSON-RPC 2.0 format:
{
    "jsonrpc": "2.0", 
    "id": 0,  # Must match the request id
    "result": {
        "schema_version": "v1", 
        "capabilities": ["function_calling"], 
        "tool_specs": [...]
    }
}
```

Specifically, update the `handle_request` function in `filesystem_mcp_fixed.py` to properly format the response according to the JSON-RPC 2.0 specification.

## Additional Considerations

1. **Version Compatibility**: Check if the server is supporting the protocol version requested by the client (`2024-11-05`)
2. **Error Handling**: Improve error messages when version or capability negotiation fails
3. **Logging**: Keep logs separate from the JSON-RPC communication channel

## References

1. [MCP Lifecycle](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle)
2. [MCP Transports](https://modelcontextprotocol.io/docs/concepts/transports)
3. [GitHub Issue: Server Disconnected](https://github.com/orgs/modelcontextprotocol/discussions/308)

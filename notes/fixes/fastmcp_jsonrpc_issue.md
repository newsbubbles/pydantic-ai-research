# FastMCP JSON-RPC Format Issue Analysis

## Date: 2025-06-20

## Problem Summary

We've discovered that the fundamental issue with the MCP server initialization is related to the **JSON-RPC 2.0 format mismatch** between the PydanticAI client and the custom MCP server implementation. This issue appears to be common in the FastMCP ecosystem and has been reported by several users.

## Key Insights from Log Analysis

### Initial Observations

1. The PydanticAI client sends a proper JSON-RPC 2.0 request with:
   ```json
   {
     "method": "initialize",
     "params": {
       "protocolVersion": "2025-03-26",
       "capabilities": {},
       "clientInfo": {"name": "mcp", "version": "0.1.0"}
     },
     "jsonrpc": "2.0",
     "id": 0
   }
   ```

2. The server responds with an **incorrectly formatted** response:
   ```json
   {
     "schema_version": "v1", 
     "capabilities": ["function_calling"], 
     "tool_specs": [...]
   }
   ```

3. Per the MCP protocol specification, the response should be in JSON-RPC 2.0 format:
   ```json
   {
     "jsonrpc": "2.0",
     "id": 0,
     "result": {
       "protocolVersion": "2025-03-26",
       "capabilities": {...},
       "tool_specs": [...]
     }
   }
   ```

### Protocol Version Evolution

1. First test run: Client requested protocol version "2024-11-05"
2. After pydantic-ai upgrade: Client requested protocol version "2025-03-26"
3. Current MCP specification version: "2025-06-18"

This indicates that the protocol has gone through multiple versions, and each version may have different formatting requirements.

## Research Findings on FastMCP Issues

1. **Common Issue Pattern**: Multiple users have reported similar issues with FastMCP servers not correctly formatting JSON-RPC responses, leading to initialization failures with clients like PydanticAI, Claude Desktop, and others.

2. **Protocol Version Mismatch**: Issues have been reported with clients requesting newer protocol versions (like "2025-03-26") that some server implementations don't properly support.

3. **JSON-RPC Format Requirements**: The MCP specification clearly requires strict adherence to JSON-RPC 2.0 format, including:
   - The `jsonrpc` field with value "2.0"
   - The `id` field matching the request id
   - Responses wrapped in a `result` object
   - Error responses in a specific format with error codes

4. **Schema Formatting**: The MCP server tooling schemas need to follow specific JSON Schema conventions to be compatible with client expectations.

## Evolution of Our Understanding

1. **Initial Hypothesis**: We initially thought there might be a Python version compatibility issue or a PydanticAI version problem.

2. **Testing**: Upgrading PydanticAI changed the protocol version requested but didn't resolve the fundamental issue.

3. **Root Cause Identification**: We determined that the real issue is with the JSON-RPC format in the MCP server response, regardless of protocol version or client version.

## Solution Approach

The key to solving this issue is ensuring proper JSON-RPC 2.0 formatting in the server response. Specifically:

1. Modify the `handle_request` function in `filesystem_mcp_fixed.py` to format responses according to the JSON-RPC 2.0 specification:
   ```python
   response = {
       "jsonrpc": "2.0",
       "id": request_id,
       "result": {
           "protocolVersion": requested_version,
           "capabilities": {...},
           "tool_specs": [...]
       }
   }
   ```

2. Ensure all other responses (like function execution results and errors) also follow the JSON-RPC 2.0 format.

## Lessons Learned

1. **Follow the Protocol**: MCP implementations need to strictly adhere to the JSON-RPC 2.0 format as specified in the MCP documentation.

2. **Version Negotiation**: Proper handling of protocol version negotiation is important for compatibility.

3. **Logging**: Detailed logging of the exact JSON sent and received is crucial for debugging MCP issues.

## References

1. [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
2. [MCP Transports Documentation](https://modelcontextprotocol.io/docs/concepts/transports)
3. [MCP Protocol Version Specification](https://modelcontextprotocol.io/specification/versioning)
4. [MCP Lifecycle](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle)

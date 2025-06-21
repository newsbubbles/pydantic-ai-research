# PydanticAI Filesystem Agent Tests

This directory contains test scripts for demonstrating PydanticAI capabilities with a simple filesystem MCP server.

## Files

- `mcp_servers/filesystem_mcp.py` - A basic filesystem MCP server that provides file operations
- `agent_test.py` - Test script for delta streaming with the filesystem agent
- `agent_structured_test.py` - Test script for structured data streaming with the filesystem agent

## Setup

1. Ensure you have pydantic-ai installed:

```bash
pip install pydantic-ai
```

2. Set up your environment variables:

```bash
# Either set OpenRouter API key
export OPENROUTER_API_KEY=your-openrouter-key

# Or set OpenAI API key
export OPENAI_API_KEY=your-openai-key
```

3. Make the script files executable:

```bash
chmod +x agent_test.py agent_structured_test.py mcp_servers/filesystem_mcp.py
```

## Running the Tests

### Delta Streaming Test

Run the delta streaming test with:

```bash
./agent_test.py
```

This will start an interactive session where you can ask the agent to perform file operations. The agent's responses will be streamed to the console in real-time using delta streaming.

Example commands to try:

- `List the files in the current directory`
- `Create a new file called test.txt with the content "Hello, World!"`
- `Read the content of test.txt`
- `Get information about this directory`

### Structured Data Streaming Test

Run the structured data streaming test with:

```bash
./agent_structured_test.py
```

This test focuses on structured data analysis. Simply enter a directory path when prompted, and the agent will analyze it and return structured information.

The structured output includes:
- Directory path
- List of files with details
- Total file count
- Total size
- Summary of contents

## How It Works

1. The filesystem MCP server implements file operations as tools
2. The agent connects to the MCP server to access these tools
3. Delta streaming shows the agent's response as it's generated
4. Structured data streaming provides real-time updates as the structured response is built

## Notes

- The MCP server is a standalone Python script that communicates with the agent via stdin/stdout
- Error handling is implemented to gracefully handle issues
- The structured test uses TypedDict and Pydantic models to define the output structure
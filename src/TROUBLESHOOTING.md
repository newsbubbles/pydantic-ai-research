# Troubleshooting PydanticAI Tests

## Common Issues and Solutions

### 1. Scripts Hanging After MCP Server Initialization

**Symptoms:**
- Script starts and logs show "Received request with method: initialize" but then nothing happens
- No prompt appears for user input
- Process seems to be frozen

**Possible Causes:**
- Communication issues between the agent and MCP server
- Environment variables not properly set
- Python version compatibility issues
- API key issues

**Solutions:**
- Check the logs in the `logs` directory for detailed error messages
- Ensure you have set either the OPENAI_API_KEY or OPENROUTER_API_KEY environment variables
- Try using a simpler model (the fixed scripts use Claude-3-Haiku or GPT-3.5-Turbo instead of larger models)
- Make sure your Python version is 3.10+ (some features require newer Python versions)
- Restart your terminal to ensure environment variables are properly set

### 2. Permission Issues

**Symptoms:**
- "Permission denied" errors when running scripts

**Solution:**
- Make the scripts executable with the following commands:
  ```bash
  chmod +x src/agent_test_fixed.py
  chmod +x src/agent_structured_test_fixed.py
  chmod +x src/mcp_servers/filesystem_mcp_fixed.py
  chmod +x src/run_tests.sh
  ```

### 3. API Key Issues

**Symptoms:**
- Authentication errors
- Script fails with API key related errors

**Solution:**
- Set your API keys correctly in your environment:
  ```bash
  # For OpenRouter
  export OPENROUTER_API_KEY=your-openrouter-key
  
  # OR for OpenAI
  export OPENAI_API_KEY=your-openai-key
  ```

### 4. Dependencies Not Installed

**Symptoms:**
- Import errors when running the scripts

**Solution:**
- Install the required dependencies:
  ```bash
  pip install pydantic-ai pydantic "typing-extensions>=4.8.0"
  ```

## Using the Diagnostics Logs

The fixed scripts log detailed information to the `logs` directory. You can examine these logs to diagnose issues:

- `logs/agent_test.log` - Logs from the delta streaming test
- `logs/agent_structured_test.log` - Logs from the structured streaming test
- `logs/filesystem_mcp.log` - Logs from the filesystem MCP server

Look for ERROR or WARNING level messages that might indicate what's going wrong.

## Using the Runner Script

For simplicity, you can use the provided runner script to run the tests:

```bash
chmod +x src/run_tests.sh
./src/run_tests.sh
```

This script will:
- Make all necessary scripts executable
- Check for API keys in the environment
- Provide a menu to select which test to run

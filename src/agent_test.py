#!/usr/bin/env python3

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

import os
import asyncio
import logging
import traceback
from pathlib import Path
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("agent_test.log"), logging.StreamHandler()]
)
logger = logging.getLogger("agent_test")

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY and not OPENAI_API_KEY:
    raise ValueError("Either OPENROUTER_API_KEY or OPENAI_API_KEY must be set")

# Setup agent system prompt
def load_agent_prompt() -> str:
    """Create a simple system prompt for the filesystem agent"""
    time_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return f"""
    # Filesystem Agent

    You are a helpful assistant that specializes in working with the filesystem.
    Current time: {time_now}

    ## Capabilities
    - You can list files and directories
    - You can read file contents
    - You can write content to files
    - You can get information about files and directories

    ## Limitations
    - You can only work with files that are accessible to this script
    - You cannot execute arbitrary code
    - You cannot access the internet

    ## Instructions
    - When asked to work with files, use the appropriate tools
    - Clearly explain what you're doing when using tools
    - When showing file or directory listings, format them nicely
    - When showing file contents, display them in an appropriate format
    """

# Set up model and provider
def create_model():
    """Create the model with the appropriate provider"""
    if OPENROUTER_API_KEY:
        provider = OpenAIProvider(
            base_url='https://openrouter.ai/api/v1',
            api_key=OPENROUTER_API_KEY
        )
        logger.info("Using OpenRouter as provider")
        model_name = 'anthropic/claude-3-sonnet'  # Using Claude 3 Sonnet via OpenRouter
    else:
        provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        logger.info("Using OpenAI as provider")
        model_name = 'gpt-4o'  # Default to GPT-4o if using OpenAI directly
    
    return OpenAIModel(model_name, provider=provider)

# Create the agent
def create_agent():
    """Create the agent with the filesystem MCP server"""
    model = create_model()
    logger.info(f"Created model: {model}")
    
    # Get the absolute path to the MCP server script
    script_dir = Path(__file__).parent.absolute()
    mcp_server_path = script_dir / "mcp_servers" / "filesystem_mcp.py"
    
    # Ensure the MCP server script is executable
    if not os.access(mcp_server_path, os.X_OK):
        logger.info(f"Making MCP server script executable: {mcp_server_path}")
        os.chmod(mcp_server_path, 0o755)
    
    # Create the MCP server
    mcp_server = MCPServerStdio('python', [str(mcp_server_path)])
    logger.info(f"Created MCP server with script: {mcp_server_path}")
    
    # Create the agent
    agent_prompt = load_agent_prompt()
    agent = Agent(model, mcp_servers=[mcp_server], system_prompt=agent_prompt)
    logger.info("Created agent with filesystem MCP server")
    
    return agent

async def main():
    """Run the filesystem agent with delta streaming"""
    agent = create_agent()
    
    print("\nFilesystem Agent (Delta Streaming)")
    print("=====================================\n")
    print("Type 'exit' to quit the program.\n")
    
    # Run the agent with MCP servers
    async with agent.run_mcp_servers():
        message_history = []
        result = None
        
        while True:
            # Print previous result if available
            if result:
                print("\n")
            
            # Get user input
            user_input = input("> ")
            if user_input.lower() == 'exit':
                break
            
            # Run the agent with streaming
            try:
                print("\nAgent: ", end="", flush=True)
                async with agent.run_stream(user_input, message_history=message_history) as result_stream:
                    # Initialize a variable to accumulate the complete response
                    complete_response = ""
                    
                    # Use delta streaming to show output as it's generated
                    async for delta in result_stream.stream_text(delta=True):
                        print(delta, end="", flush=True)
                        complete_response += delta
                    
                    # Get the full response and update message history
                    result = result_stream
                    message_history.append({"role": "user", "content": user_input})
                    message_history.append({"role": "assistant", "content": complete_response})
                    
                    # Keep message history limited to last 10 messages
                    if len(message_history) > 10:
                        message_history = message_history[-10:]
            
            except Exception as e:
                print(f"\n\nError: {str(e)}")
                logger.error(f"Error running agent: {str(e)}")
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.messages import ModelMessage, SystemPromptPart, UserPromptPart, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.agent import AgentRunResult

import os
import asyncio
import logging
import traceback
import time
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict

# Ensure logs directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Increased to DEBUG for more verbose logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "debug.log"),  # Use the logs directory for log files
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_test_fixed")

# Log to stdout
logging.getLogger('pydantic_ai').setLevel(logging.DEBUG)
logging.getLogger('asyncio').setLevel(logging.DEBUG)

# Log script startup
logger.info("=== Agent Test Script Starting ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logger.info(f"OPENAI_API_KEY set: {'Yes' if OPENAI_API_KEY else 'No'}")
logger.info(f"OPENROUTER_API_KEY set: {'Yes' if OPENROUTER_API_KEY else 'No'}")

if not OPENROUTER_API_KEY and not OPENAI_API_KEY:
    logger.error("No API keys found in environment variables")
    raise ValueError("Either OPENROUTER_API_KEY or OPENAI_API_KEY must be set")

# Function to filter message history
def filtered_message_history(
    result: Optional[AgentRunResult], 
    limit: Optional[int] = None, 
    include_tool_messages: bool = True
) -> Optional[List[ModelMessage]]:
    """
    Filter and limit the message history from an AgentRunResult.
    
    Args:
        result: The AgentRunResult object with message history
        limit: Optional int, if provided returns only system message + last N messages
        include_tool_messages: Whether to include tool messages in the history
        
    Returns:
        Filtered list of messages in the format expected by the agent
    """
    if result is None:
        return None
        
    # Get all messages
    messages: List[ModelMessage] = result.all_messages()
    
    # Extract system message (always the first one with role="system")
    system_message = next((msg for msg in messages if any(isinstance(part, SystemPromptPart) for part in msg.parts)), None)
    
    # Filter non-system messages
    non_system_messages = [msg for msg in messages if not any(isinstance(part, SystemPromptPart) for part in msg.parts)]
    
    # Apply tool message filtering if requested
    if not include_tool_messages:
        non_system_messages = [msg for msg in non_system_messages if not any(isinstance(part, ToolCallPart) or isinstance(part, ToolReturnPart) for part in msg.parts)]
    
    # Apply limit if specified, but ensure paired tool calls and returns stay together
    if limit is not None and limit > 0:
        # Identify tool call IDs and their corresponding return parts
        tool_call_ids = {}
        tool_return_ids = set()
        
        for i, msg in enumerate(non_system_messages):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    tool_call_ids[part.tool_call_id] = i
                elif isinstance(part, ToolReturnPart):
                    tool_return_ids.add(part.tool_call_id)
        
        # Take the last 'limit' messages but ensure we include paired messages
        if len(non_system_messages) > limit:
            included_indices = set(range(len(non_system_messages) - limit, len(non_system_messages)))
            
            # Include any missing tool call messages for tool returns that are included
            for i, msg in enumerate(non_system_messages):
                if i in included_indices:
                    for part in msg.parts:
                        if isinstance(part, ToolReturnPart) and part.tool_call_id in tool_call_ids:
                            included_indices.add(tool_call_ids[part.tool_call_id])
            
            # Create a new list with only the included messages
            non_system_messages = [msg for i, msg in enumerate(non_system_messages) if i in included_indices]
    
    # Combine system message with other messages
    result_messages = []
    if system_message:
        result_messages.append(system_message)
    result_messages.extend(non_system_messages)
    
    return result_messages

# Setup agent system prompt
def load_agent_prompt() -> str:
    """Create a simple system prompt for the filesystem agent"""
    time_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    prompt = f"""
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
    logger.info("Agent prompt loaded")
    return prompt

# Set up model and provider
def create_model():
    """Create the model with the appropriate provider"""
    try:
        if OPENROUTER_API_KEY:
            logger.info("Creating model with OpenRouter provider")
            provider = OpenAIProvider(
                base_url='https://openrouter.ai/api/v1',
                api_key=OPENROUTER_API_KEY
            )
            logger.info("OpenRouter provider created")
            model_name = 'anthropic/claude-3-haiku'  # Using a simpler/faster model for testing
        else:
            logger.info("Creating model with OpenAI provider")
            provider = OpenAIProvider(api_key=OPENAI_API_KEY)
            logger.info("OpenAI provider created")
            model_name = 'gpt-3.5-turbo'  # Using a faster model for testing
        
        logger.info(f"Creating model with name: {model_name}")
        model = OpenAIModel(model_name, provider=provider)
        logger.info("Model created successfully")
        return model
    except Exception as e:
        logger.error(f"Error creating model: {str(e)}")
        raise

# Create the agent
def create_agent():
    """Create the agent with the filesystem MCP server"""
    try:
        logger.info("Creating agent...")
        model = create_model()
        
        # Get the absolute path to the MCP server script
        script_dir = Path(__file__).parent.absolute()
        mcp_server_path = script_dir / "mcp_servers" / "filesystem_mcp.py"  # Use the new version
        logger.info(f"MCP server path: {mcp_server_path}")
        
        # Ensure the MCP server script exists
        if not mcp_server_path.exists():
            logger.error(f"MCP server script not found at: {mcp_server_path}")
            raise FileNotFoundError(f"MCP server script not found at: {mcp_server_path}")
            
        # Ensure the MCP server script is executable
        if not os.access(mcp_server_path, os.X_OK):
            logger.info(f"Making MCP server script executable: {mcp_server_path}")
            os.chmod(mcp_server_path, 0o755)
        
        # Set environment variables for the MCP server
        mcp_env = os.environ.copy()
        mcp_env["LOG_DIR"] = str(log_dir)  # Pass log directory to MCP server
        
        # Create the MCP server
        logger.info("Creating MCP server...")
        mcp_server = MCPServerStdio('python', [str(mcp_server_path)], env=mcp_env)
        logger.info("MCP server created")
        
        # Create the agent
        agent_prompt = load_agent_prompt()
        logger.info("Creating agent with MCP server and prompt...")
        agent = Agent(model, mcp_servers=[mcp_server], system_prompt=agent_prompt)
        logger.info("Agent created successfully")
        
        return agent
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise

async def main():
    """Run the filesystem agent with delta streaming"""
    try:
        logger.info("Starting main function")
        agent = create_agent()
        
        print("\nFilesystem Agent (Delta Streaming)")
        print("=====================================\n")
        print("Type 'exit' to quit the program.\n")
        
        # Add timeout for starting MCP servers
        logger.info("Starting MCP servers...")
        try:
            # Run the agent with MCP servers
            async with asyncio.timeout(30):  # 30-second timeout for starting MCP servers
                async with agent.run_mcp_servers() as mcp_manager:
                    logger.info("MCP servers started successfully")
                    
                    result = None
                    
                    while True:
                        # Print previous result if available
                        if result:
                            print("\n")
                        
                        # Get user input
                        print("> ", end="", flush=True)
                        user_input = input()
                        logger.info(f"User input: {user_input}")
                        
                        if user_input.lower() == 'exit':
                            logger.info("User requested exit")
                            break
                        
                        # Run the agent with streaming
                        try:
                            print("\nAgent: ", end="", flush=True)
                            logger.info("Starting agent.run_stream...")
                            
                            # Use the filtered message history function
                            filtered_messages = filtered_message_history(
                                result,
                                limit=8,  # Last 8 non-system messages
                                include_tool_messages=True  # Include tool messages
                            )
                            
                            # Log the number of messages being used
                            if filtered_messages:
                                logger.info(f"Using {len(filtered_messages)} filtered messages in history")
                            else:
                                logger.info("No message history available for this run")
                            
                            # Add timeout for agent run
                            async with asyncio.timeout(60):  # 60-second timeout for agent response
                                async with agent.run_stream(user_input, message_history=filtered_messages) as result_stream:
                                    logger.info("Agent run_stream started, beginning to stream response...")
                                    
                                    # Initialize a variable to accumulate the complete response
                                    complete_response = ""
                                    
                                    # Use delta streaming to show output as it's generated
                                    async for delta in result_stream.stream_text(delta=True):
                                        print(delta, end="", flush=True)
                                        complete_response += delta
                                    
                                    # Get the full response
                                    result = result_stream
                                    logger.info(f"Complete response received, length: {len(complete_response)}")
                                    
                        except asyncio.TimeoutError:
                            print("\n\nError: Response timed out. Please try again.")
                            logger.error("Timeout while waiting for agent response")
                        except Exception as e:
                            print(f"\n\nError: {str(e)}")
                            logger.error(f"Error running agent: {str(e)}")
                            traceback.print_exc()
        
        except asyncio.TimeoutError:
            print("\nError: Timed out while starting MCP servers. Please check the logs and try again.")
            logger.error("Timeout while starting MCP servers")
            return
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        logger.error(f"Error in main function: {str(e)}")
        traceback.print_exc()
    finally:
        logger.info("Main function completed")

if __name__ == "__main__":
    logger.info("Running main function")
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
        print("\nProgram interrupted by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        traceback.print_exc()
    finally:
        logger.info("Program exit")

#!/usr/bin/env python3

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.messages import ToolCallPart, TextPart, ModelResponse

import os
import asyncio
import logging
import traceback
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/debug.log"), logging.StreamHandler()]
)
logger = logging.getLogger("agent_test_iter")

# Set debug level for specific loggers
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("openai").setLevel(logging.INFO)

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
    - Always provide a summary response after tool calls
    """

# Set up model and provider
def create_model():
    """Create the model with the appropriate provider"""
    logger.info("Creating model with OpenRouter provider")
    if OPENROUTER_API_KEY:
        try:
            provider = OpenAIProvider(
                base_url='https://openrouter.ai/api/v1',
                api_key=OPENROUTER_API_KEY
            )
            logger.info("OpenRouter provider created")
            model_name = 'anthropic/claude-3-haiku'  # Using Claude 3 Haiku via OpenRouter
            logger.info(f"Creating model with name: {model_name}")
            model = OpenAIModel(model_name, provider=provider)
            logger.info("Model created successfully")
            return model
        except Exception as e:
            logger.error(f"Error creating OpenRouter model: {str(e)}")
            raise
    else:
        try:
            provider = OpenAIProvider(api_key=OPENAI_API_KEY)
            logger.info("OpenAI provider created")
            model_name = 'gpt-4o'  # Default to GPT-4o if using OpenAI directly
            logger.info(f"Creating model with name: {model_name}")
            model = OpenAIModel(model_name, provider=provider)
            logger.info("Model created successfully")
            return model
        except Exception as e:
            logger.error(f"Error creating OpenAI model: {str(e)}")
            raise

# Create the agent
def create_agent():
    """Create the agent with the filesystem MCP server"""
    model = create_model()
    
    # Get the absolute path to the MCP server script
    script_dir = Path(__file__).parent.absolute()
    mcp_server_path = script_dir / "mcp_servers" / "filesystem_mcp.py"
    logger.info(f"MCP server path: {mcp_server_path}")
    
    # Ensure the MCP server script is executable
    if not os.access(mcp_server_path, os.X_OK):
        logger.info(f"Making MCP server script executable: {mcp_server_path}")
        os.chmod(mcp_server_path, 0o755)
    
    # Create the MCP server
    logger.info("Creating MCP server...")
    mcp_server = MCPServerStdio('python', [str(mcp_server_path)])
    logger.info("MCP server created")
    
    # Create the agent
    prompt = load_agent_prompt()
    logger.info("Agent prompt loaded")
    
    logger.info("Creating agent with MCP server and prompt...")
    agent = Agent(model, mcp_servers=[mcp_server], system_prompt=prompt)
    logger.info("Agent created successfully")
    
    return agent

class ToolStateTracker:
    """Track tool calls and their results for proper streaming output handling"""
    
    def __init__(self):
        self.tool_calls = {}
        self.tool_results = {}
        self.text_output = []
        self.final_output = ""
    
    def add_tool_call(self, tool_call: ToolCallPart):
        """Record a new tool call"""
        self.tool_calls[tool_call.tool_call_id] = {
            "tool_name": tool_call.tool_name,
            "args": tool_call.args_as_dict() if hasattr(tool_call, "args_as_dict") else tool_call.args
        }
    
    def add_tool_result(self, tool_call_id: str, result: Any):
        """Record a tool result"""
        self.tool_results[tool_call_id] = result
    
    def add_text(self, text: str):
        """Add text output"""
        self.text_output.append(text)
        self.final_output += text
    
    def get_complete_output(self) -> str:
        """Get the complete output including any text from after tool calls"""
        return self.final_output

async def run_with_iter(agent: Agent, user_input: str, message_history: Optional[List[Dict[str, Any]]] = None) -> tuple[str, List[Dict[str, Any]]]:
    """Run the agent using iter() to handle streaming with proper tool call flow
    
    This is a replacement for agent.run_stream() that properly handles the case where Claude makes a tool call
    and then needs to generate text after the tool result is returned.
    
    Args:
        agent: The PydanticAI agent
        user_input: User query/prompt
        message_history: Optional message history from previous interactions
        
    Returns:
        tuple containing (complete_output, updated_message_history)
    """
    tracker = ToolStateTracker()
    filtered_messages = message_history or []
    
    logger.info(f"User input: {user_input}")
    if message_history:
        logger.info(f"Message history contains {len(message_history)} messages")
    else:
        logger.info("No message history available for this run")
    
    print("\nAgent: ", end="", flush=True)
    
    try:
        # Use the iter() method to manually process the agent's execution graph
        async with agent.iter(user_input, message_history=filtered_messages) as agent_run:
            async for node in agent_run:
                # Handle different node types
                if agent.is_model_request_node(node):
                    # This is a request being sent to the model (no need to do anything)
                    pass
                
                elif agent.is_call_tools_node(node):
                    # This is a response from the model that might contain tool calls or text
                    model_response: ModelResponse = node.model_response
                    
                    # Process each part of the response
                    for part in model_response.parts:
                        if isinstance(part, TextPart) and part.content.strip():
                            # Display and track text output
                            print(part.content, end="", flush=True)
                            tracker.add_text(part.content)
                        
                        elif isinstance(part, ToolCallPart):
                            # Process and display tool call
                            tracker.add_tool_call(part)
                            tool_name = part.tool_name
                            args = part.args_as_dict() if hasattr(part, "args_as_dict") else part.args
                            logger.info(f"Tool call: {tool_name} with args: {json.dumps(args)}")
                            
                            # Format the args for prettier display
                            args_str = json.dumps(args, indent=2)
                            print(f"\n[Tool Call: {tool_name}]\n{args_str}\n", end="", flush=True)
                
                elif agent.is_end_node(node):
                    # End of the execution - we can retrieve the final result
                    logger.info(f"End node reached with result: {agent_run.result}")
                
                # For other node types, we just let them process normally
        
        # After the execution completes, get the final output
        complete_output = tracker.get_complete_output()
        logger.info(f"Complete output collected, length: {len(complete_output)}")
        
        # Update message history
        filtered_messages.append({"role": "user", "content": user_input})
        filtered_messages.append({"role": "assistant", "content": complete_output})
        
        # Keep message history limited to last 10 messages
        if len(filtered_messages) > 10:
            filtered_messages = filtered_messages[-10:]
        
        return complete_output, filtered_messages
    
    except Exception as e:
        logger.error(f"Error in run_with_iter: {str(e)}")
        traceback.print_exc()
        print(f"\n\nError: {str(e)}")
        return f"Error: {str(e)}", filtered_messages

async def main():
    """Run the filesystem agent with improved tool call handling"""
    logger.info("=== Agent Test Script Starting ===")
    logger.info(f"Python version: {os.sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"OPENAI_API_KEY set: {'Yes' if OPENAI_API_KEY else 'No'}")
    logger.info(f"OPENROUTER_API_KEY set: {'Yes' if OPENROUTER_API_KEY else 'No'}")
    logger.info("Running main function")
    
    try:
        logger.info("Starting main function")
        logger.info("Creating agent...")
        agent = create_agent()
        
        print("\nFilesystem Agent (Iter Streaming)")
        print("=====================================\n")
        print("Type 'exit' to quit the program.\n")
        
        # Run the agent with MCP servers
        logger.info("Starting MCP servers...")
        async with agent.run_mcp_servers():
            logger.info("MCP servers started successfully")
            message_history = []
            
            while True:
                # Get user input
                user_input = input("> ")
                if user_input.lower() == 'exit':
                    break
                
                # Run the agent using our custom iter-based function
                complete_output, message_history = await run_with_iter(agent, user_input, message_history)
                
                print("\n")  # Add a newline after the response
    
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        traceback.print_exc()
        print(f"\n\nCritical Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

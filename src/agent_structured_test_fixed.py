#!/usr/bin/env python3

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

import os
import asyncio
import logging
import traceback
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import TypedDict, List, Optional
from pydantic import BaseModel

# Ensure logs directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "agent_structured_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_structured_test")

# Log to stdout
logging.getLogger('pydantic_ai').setLevel(logging.DEBUG)
logging.getLogger('asyncio').setLevel(logging.DEBUG)

# Log script startup
logger.info("=== Agent Structured Test Script Starting ===")
logger.info(f"Python version: {sys.version}")

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logger.info(f"OPENAI_API_KEY set: {'Yes' if OPENAI_API_KEY else 'No'}")
logger.info(f"OPENROUTER_API_KEY set: {'Yes' if OPENROUTER_API_KEY else 'No'}")

if not OPENROUTER_API_KEY and not OPENAI_API_KEY:
    logger.error("No API keys found in environment variables")
    raise ValueError("Either OPENROUTER_API_KEY or OPENAI_API_KEY must be set")

# Define structured output types
class FileInfo(TypedDict):
    name: str
    path: str
    size: int
    is_directory: bool
    description: Optional[str]

class DirectoryContent(BaseModel):
    directory_path: str
    files: List[FileInfo]
    total_files: int
    total_size: int
    summary: str

# Setup agent system prompt
def load_agent_prompt() -> str:
    """Create a system prompt for the filesystem agent with structured output"""
    time_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    prompt = f"""
    # Filesystem Analysis Agent

    You are a specialized agent that analyzes filesystem content and returns structured information.
    Current time: {time_now}

    ## Capabilities
    - You can list and analyze directories
    - You can read file contents
    - You can provide structured information about filesystem contents

    ## Output Format
    When asked to analyze a directory, you will return structured information using the DirectoryContent format,
    which includes:
    - directory_path: The full path of the directory
    - files: A list of FileInfo objects with information about each file
    - total_files: The total number of files found
    - total_size: The total size of all files in bytes
    - summary: A brief summary of the directory contents

    ## Instructions
    - When asked to analyze or summarize a directory, use the appropriate tools to gather information
    - Provide a complete inventory of files with accurate details
    - Include helpful descriptions for each file based on its name, extension, or content
    - Format sizes in a human-readable way when displaying information
    - Always return properly structured data that matches the output schema
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
    """Create the agent with the filesystem MCP server and structured output type"""
    try:
        logger.info("Creating agent...")
        model = create_model()
        
        # Get the absolute path to the MCP server script
        script_dir = Path(__file__).parent.absolute()
        mcp_server_path = script_dir / "mcp_servers" / "filesystem_mcp.py"  # Use the new implementation
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
        
        # Create the agent with DirectoryContent as the output type
        agent_prompt = load_agent_prompt()
        logger.info("Creating agent with MCP server and prompt...")
        agent = Agent(
            model, 
            mcp_servers=[mcp_server], 
            system_prompt=agent_prompt,
            output_type=DirectoryContent
        )
        logger.info("Agent created successfully")
        
        return agent
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise

def format_size(size_bytes):
    """Format size in bytes to a human-readable string"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def display_directory_content(content: DirectoryContent):
    """Display directory content in a nicely formatted way"""
    print(f"\n===== Directory Analysis: {content.directory_path} =====\n")
    print(f"Summary: {content.summary}\n")
    print(f"Total Files: {content.total_files}")
    print(f"Total Size: {format_size(content.total_size)}\n")
    
    print("Files:")
    print("-" * 80)
    print(f"{'Name':<30} {'Type':<10} {'Size':<12} {'Description'}")
    print("-" * 80)
    
    for file in content.files:
        file_type = "Directory" if file["is_directory"] else "File"
        size_str = "" if file["is_directory"] else format_size(file["size"])
        print(f"{file['name']:<30} {file_type:<10} {size_str:<12} {file.get('description', '')}")

async def main():
    """Run the filesystem agent with structured streaming"""
    try:
        logger.info("Starting main function")
        agent = create_agent()
        
        print("\nFilesystem Analysis Agent (Structured Streaming)")
        print("==============================================\n")
        print("This agent returns structured information about directories.")
        print("Type a directory path to analyze, or 'exit' to quit.\n")
        
        # Add timeout for starting MCP servers
        logger.info("Starting MCP servers...")
        try:
            # Run the agent with MCP servers
            async with asyncio.timeout(30):  # 30-second timeout for starting MCP servers
                async with agent.run_mcp_servers() as mcp_manager:
                    logger.info("MCP servers started successfully")
                    
                    while True:
                        # Get user input
                        print("> ", end="", flush=True)
                        user_input = input()
                        logger.info(f"User input: {user_input}")
                        
                        if user_input.lower() == 'exit':
                            logger.info("User requested exit")
                            break
                        
                        # Process the input to ensure it's asking for directory analysis
                        if not os.path.exists(user_input):
                            print(f"\nError: Path '{user_input}' does not exist.")
                            logger.warning(f"Path does not exist: {user_input}")
                            continue
                                
                        # Formulate a clear prompt for directory analysis
                        prompt = f"Analyze the directory '{user_input}' and provide a structured summary of its contents."
                        logger.info(f"Formatted prompt: {prompt}")
                        
                        # Run the agent with structured streaming
                        try:
                            print("\nAnalyzing directory, please wait...\n")
                            logger.info("Starting agent.run_stream for structured data...")
                            
                            # Use structured streaming with timeout
                            async with asyncio.timeout(60):  # 60-second timeout for agent response
                                async with agent.run_stream(prompt) as result_stream:
                                    logger.info("Agent run_stream started for structured data")
                                    
                                    # Display partial validations as they come in
                                    print("Streaming partial results:\n")
                                    progress_count = 0
                                    
                                    # Stream structured results
                                    async for response in result_stream.stream_structured():
                                        # Show progress
                                        progress_count += 1
                                        print(f"\rProcessing... ({progress_count} updates)", end="", flush=True)
                                        
                                        # Try to validate the partial response
                                        try:
                                            partial = result_stream.validate_structured_output(
                                                DirectoryContent, 
                                                allow_partial=True
                                            )
                                            
                                            if partial and partial.files:
                                                # Show a simple progress indicator
                                                files_analyzed = len(partial.files) if partial.files else 0
                                                print(f"\rProgress: Analyzed {files_analyzed} files so far...", end="", flush=True)
                                        except Exception as validation_err:
                                            # Validation errors are expected for partial results
                                            logger.debug(f"Partial validation error: {str(validation_err)}")
                                    
                                    # Get and display the final result
                                    logger.info("Structured streaming completed")
                                    result = result_stream.output
                                    logger.info(f"Final result: {result.model_dump_json()}")
                                    print("\n\nFinal analysis complete!\n")
                                    display_directory_content(result)
                        
                        except asyncio.TimeoutError:
                            print("\n\nError: Response timed out. Please try again with a smaller directory.")
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

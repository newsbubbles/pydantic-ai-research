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
from pathlib import Path
from datetime import datetime, timezone
from typing import TypedDict, List, Optional
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("agent_structured_test.log"), logging.StreamHandler()]
)
logger = logging.getLogger("agent_structured_test")

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY and not OPENAI_API_KEY:
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
    return f"""
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
    """Create the agent with the filesystem MCP server and structured output type"""
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
    
    # Create the agent with DirectoryContent as the output type
    agent_prompt = load_agent_prompt()
    agent = Agent(
        model, 
        mcp_servers=[mcp_server], 
        system_prompt=agent_prompt,
        output_type=DirectoryContent
    )
    logger.info("Created agent with filesystem MCP server and structured output type")
    
    return agent

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
    agent = create_agent()
    
    print("\nFilesystem Analysis Agent (Structured Streaming)")
    print("==============================================\n")
    print("This agent returns structured information about directories.")
    print("Type a directory path to analyze, or 'exit' to quit.\n")
    
    # Run the agent with MCP servers
    async with agent.run_mcp_servers():
        while True:
            # Get user input
            user_input = input("> ")
            if user_input.lower() == 'exit':
                break
            
            # Process the input to ensure it's asking for directory analysis
            if not os.path.exists(user_input):
                print(f"\nError: Path '{user_input}' does not exist.")
                continue
                
            # Formulate a clear prompt for directory analysis
            prompt = f"Analyze the directory '{user_input}' and provide a structured summary of its contents."
            
            # Run the agent with structured streaming
            try:
                print("\nAnalyzing directory, please wait...\n")
                
                # Use structured streaming
                async with agent.run_stream(prompt) as result_stream:
                    # Display partial validations as they come in
                    print("Streaming partial results:\n")
                    
                    async for response in result_stream.stream_structured():
                        # Try to validate the partial response
                        try:
                            partial = result_stream.validate_structured_output(
                                DirectoryContent, 
                                allow_partial=True
                            )
                            
                            if partial:
                                # Show a simple progress indicator
                                files_analyzed = len(partial.files) if partial.files else 0
                                print(f"\rProgress: Analyzed {files_analyzed} files so far...", end="", flush=True)
                        except Exception as validation_err:
                            # Validation errors are expected for partial results
                            pass
                    
                    # Get and display the final result
                    result = result_stream.output
                    print("\n\nFinal analysis complete!\n")
                    display_directory_content(result)
                    
            except Exception as e:
                print(f"\n\nError: {str(e)}")
                logger.error(f"Error running agent: {str(e)}")
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

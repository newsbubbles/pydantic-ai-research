#!/usr/bin/env python3

import json
import sys
import os
import logging
import traceback
from typing import Dict, Any, List, Optional
from pathlib import Path

# Set up logging
def setup_logging():
    # Get log directory from environment or default to current directory
    log_dir = os.environ.get("LOG_DIR", ".")
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    log_file = log_path / "filesystem_mcp.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,  # Increased to DEBUG for more verbose logs
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stderr)  # Log errors to stderr
        ]
    )
    logger = logging.getLogger("filesystem_mcp")
    
    # Log startup information
    logger.info("=== Filesystem MCP Server Starting ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    return logger

# Initialize logging
logger = setup_logging()

# Tool implementations
def list_files(directory: str = ".") -> Dict[str, Any]:
    """List files and directories in the specified directory"""
    logger.info(f"Listing files in: {directory}")
    try:
        path = Path(directory)
        if not path.exists():
            logger.warning(f"Directory not found: {directory}")
            return {"error": f"Directory '{directory}' not found"}
            
        items = list(path.iterdir())
        files = [item.name for item in items if item.is_file()]
        directories = [item.name for item in items if item.is_dir()]
        
        logger.info(f"Found {len(files)} files and {len(directories)} directories in {directory}")
        
        return {
            "files": files,
            "directories": directories,
            "path": str(path.absolute())
        }
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

def read_file(file_path: str) -> Dict[str, Any]:
    """Read the contents of a file"""
    logger.info(f"Reading file: {file_path}")
    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return {"error": f"File '{file_path}' not found"}
            
        if not path.is_file():
            logger.warning(f"Not a file: {file_path}")
            return {"error": f"'{file_path}' is not a file"}
            
        content = path.read_text()
        logger.info(f"Successfully read {len(content)} bytes from {file_path}")
        
        return {
            "content": content,
            "size": path.stat().st_size,
            "path": str(path.absolute())
        }
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """Write content to a file"""
    logger.info(f"Writing to file: {file_path}")
    try:
        path = Path(file_path)
        
        # Create parent directories if they don't exist
        if not path.parent.exists():
            logger.info(f"Creating parent directories for: {file_path}")
            path.parent.mkdir(parents=True)
        
        path.write_text(content)
        logger.info(f"Successfully wrote {len(content)} bytes to {file_path}")
        
        return {
            "success": True,
            "message": f"Successfully wrote {len(content)} bytes to {file_path}",
            "path": str(path.absolute())
        }
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get information about a file"""
    logger.info(f"Getting file info: {file_path}")
    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return {"error": f"File '{file_path}' not found"}
            
        stat = path.stat()
        logger.info(f"Successfully got file info for {file_path}")
        
        return {
            "name": path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "path": str(path.absolute())
        }
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

# Tool specifications
def get_tool_specs() -> List[Dict[str, Any]]:
    """Get specifications for all available tools"""
    logger.info("Getting tool specifications")
    return [
        {
            "name": "list_files",
            "description": "List files and directories in the specified directory",
            "input_schema": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path to list (default: current directory)"}
                }
            }
        },
        {
            "name": "read_file",
            "description": "Read the contents of a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to read"}
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "write_file",
            "description": "Write content to a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write to the file"}
                },
                "required": ["file_path", "content"]
            }
        },
        {
            "name": "get_file_info",
            "description": "Get information about a file or directory",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file or directory"}
                },
                "required": ["file_path"]
            }
        }
    ]

# Request handling
def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming MCP requests"""
    method = request.get("method")
    logger.info(f"Handling request with method: {method}")
    
    if method == "initialize":
        # Return capabilities and tool specs
        logger.info("Processing initialize request")
        response = {
            "schema_version": "v1",
            "capabilities": ["function_calling"],
            "tool_specs": get_tool_specs()
        }
        logger.info("Initialize response prepared")
        return response
    
    elif method == "execute_function":
        # Execute the requested function and return result
        function_name = request.get("function_name")
        params = request.get("parameters", {})
        
        logger.info(f"Executing function: {function_name} with params: {params}")
        
        try:
            if function_name == "list_files":
                result = list_files(**params)
                return {"result": result}
            elif function_name == "read_file":
                result = read_file(**params)
                return {"result": result}
            elif function_name == "write_file":
                result = write_file(**params)
                return {"result": result}
            elif function_name == "get_file_info":
                result = get_file_info(**params)
                return {"result": result}
            else:
                logger.warning(f"Unknown function: {function_name}")
                return {"error": f"Unknown function: {function_name}"}
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}
    else:
        logger.warning(f"Unknown method: {method}")
        return {"error": f"Unknown method: {method}"}

def main():
    """Main MCP server loop"""
    logger.info("Filesystem MCP Server main loop starting")
    
    # Log where stdin/stdout are pointing
    logger.info(f"stdin isatty: {sys.stdin.isatty()}")
    logger.info(f"stdout isatty: {sys.stdout.isatty()}")
    
    try:
        while True:
            # Read a line from stdin
            logger.debug("Waiting for input line...")
            line = sys.stdin.readline()
            
            # Exit if stdin is closed
            if not line:
                logger.info("End of input stream, shutting down")
                break
                
            logger.debug(f"Received input line: {line.strip()}")
            
            try:
                # Parse the JSON request
                request = json.loads(line)
                
                # Handle the request
                response = handle_request(request)
                
                # Send the response
                response_json = json.dumps(response)
                logger.debug(f"Sending response: {response_json}")
                print(response_json)
                sys.stdout.flush()
                logger.debug("Response sent and flushed")
                
            except json.JSONDecodeError as e:
                # Handle JSON parsing errors
                logger.error(f"Error decoding JSON: {str(e)}")
                logger.error(f"Line content: {line.strip()}")
                error_response = json.dumps({"error": f"Invalid JSON: {str(e)}"})
                print(error_response)
                sys.stdout.flush()
                
            except Exception as e:
                # Handle other errors
                logger.error(f"Unexpected error: {str(e)}")
                traceback.print_exc()
                error_response = json.dumps({"error": f"Server error: {str(e)}"})
                print(error_response)
                sys.stdout.flush()
    
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
        traceback.print_exc()
    finally:
        logger.info("Filesystem MCP Server shutting down")

# Make the script executable
if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import os
import sys
import logging
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP, Context

# Define Pydantic models for requests and responses
class ListFilesRequest(BaseModel):
    directory: Optional[str] = Field(
        default=".", 
        description="Directory path to list (default: current directory)"
    )

class ListFilesResponse(BaseModel):
    files: List[str] = Field(..., description="List of files in the directory")
    directories: List[str] = Field(..., description="List of directories in the directory")
    path: str = Field(..., description="Absolute path of the directory")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class ReadFileRequest(BaseModel):
    file_path: str = Field(..., description="Path to the file to read")

class ReadFileResponse(BaseModel):
    content: Optional[str] = Field(None, description="Content of the file")
    size: Optional[int] = Field(None, description="Size of the file in bytes")
    path: Optional[str] = Field(None, description="Absolute path of the file")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class WriteFileRequest(BaseModel):
    file_path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")

class WriteFileResponse(BaseModel):
    success: bool = Field(..., description="Whether the write operation was successful")
    message: str = Field(..., description="Message about the write operation")
    path: Optional[str] = Field(None, description="Absolute path of the file")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class GetFileInfoRequest(BaseModel):
    file_path: str = Field(..., description="Path to the file or directory")

class GetFileInfoResponse(BaseModel):
    name: Optional[str] = Field(None, description="Name of the file or directory")
    size: Optional[int] = Field(None, description="Size of the file in bytes")
    modified: Optional[float] = Field(None, description="Last modified timestamp")
    is_file: Optional[bool] = Field(None, description="Whether the path is a file")
    is_dir: Optional[bool] = Field(None, description="Whether the path is a directory")
    path: Optional[str] = Field(None, description="Absolute path of the file or directory")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Setup logging for application lifecycle
@asynccontextmanager
async def filesystem_lifespan(server: FastMCP):
    # Set up logging
    log_dir = os.environ.get("LOG_DIR", ".")
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    log_file = log_path / "filesystem_mcp.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stderr)
        ]
    )
    logger = logging.getLogger("filesystem_mcp")
    
    # Log startup information
    logger.info("=== Filesystem MCP Server Starting ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    try:
        # Yield the logger so it can be used in tool functions
        yield {"logger": logger}
    finally:
        logger.info("=== Filesystem MCP Server Shutting Down ===")

# Create FastMCP server with lifespan
mcp = FastMCP("Filesystem Server", lifespan=filesystem_lifespan)

@mcp.tool()
def list_files(request: ListFilesRequest, ctx: Context) -> ListFilesResponse:
    """List files and directories in the specified directory"""
    logger = ctx.lifespan_context["logger"]
    logger.info(f"Listing files in: {request.directory}")
    
    try:
        path = Path(request.directory)
        if not path.exists():
            logger.warning(f"Directory not found: {request.directory}")
            return ListFilesResponse(
                files=[],
                directories=[],
                path=str(path),
                error=f"Directory '{request.directory}' not found"
            )
            
        items = list(path.iterdir())
        files = [item.name for item in items if item.is_file()]
        directories = [item.name for item in items if item.is_dir()]
        
        logger.info(f"Found {len(files)} files and {len(directories)} directories in {request.directory}")
        
        return ListFilesResponse(
            files=files,
            directories=directories,
            path=str(path.absolute())
        )
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        traceback.print_exc()
        return ListFilesResponse(
            files=[],
            directories=[],
            path=str(Path(request.directory)),
            error=str(e)
        )

@mcp.tool()
def read_file(request: ReadFileRequest, ctx: Context) -> ReadFileResponse:
    """Read the contents of a file"""
    logger = ctx.lifespan_context["logger"]
    logger.info(f"Reading file: {request.file_path}")
    
    try:
        path = Path(request.file_path)
        if not path.exists():
            logger.warning(f"File not found: {request.file_path}")
            return ReadFileResponse(
                error=f"File '{request.file_path}' not found"
            )
            
        if not path.is_file():
            logger.warning(f"Not a file: {request.file_path}")
            return ReadFileResponse(
                error=f"'{request.file_path}' is not a file"
            )
            
        content = path.read_text()
        logger.info(f"Successfully read {len(content)} bytes from {request.file_path}")
        
        return ReadFileResponse(
            content=content,
            size=path.stat().st_size,
            path=str(path.absolute())
        )
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        traceback.print_exc()
        return ReadFileResponse(
            error=str(e)
        )

@mcp.tool()
def write_file(request: WriteFileRequest, ctx: Context) -> WriteFileResponse:
    """Write content to a file"""
    logger = ctx.lifespan_context["logger"]
    logger.info(f"Writing to file: {request.file_path}")
    
    try:
        path = Path(request.file_path)
        
        # Create parent directories if they don't exist
        if not path.parent.exists():
            logger.info(f"Creating parent directories for: {request.file_path}")
            path.parent.mkdir(parents=True)
        
        path.write_text(request.content)
        logger.info(f"Successfully wrote {len(request.content)} bytes to {request.file_path}")
        
        return WriteFileResponse(
            success=True,
            message=f"Successfully wrote {len(request.content)} bytes to {request.file_path}",
            path=str(path.absolute())
        )
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        traceback.print_exc()
        return WriteFileResponse(
            success=False,
            message=f"Failed to write to {request.file_path}",
            error=str(e)
        )

@mcp.tool()
def get_file_info(request: GetFileInfoRequest, ctx: Context) -> GetFileInfoResponse:
    """Get information about a file or directory"""
    logger = ctx.lifespan_context["logger"]
    logger.info(f"Getting file info: {request.file_path}")
    
    try:
        path = Path(request.file_path)
        if not path.exists():
            logger.warning(f"File or directory not found: {request.file_path}")
            return GetFileInfoResponse(
                error=f"File or directory '{request.file_path}' not found"
            )
            
        stat = path.stat()
        logger.info(f"Successfully got file info for {request.file_path}")
        
        return GetFileInfoResponse(
            name=path.name,
            size=stat.st_size,
            modified=stat.st_mtime,
            is_file=path.is_file(),
            is_dir=path.is_dir(),
            path=str(path.absolute())
        )
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        traceback.print_exc()
        return GetFileInfoResponse(
            error=str(e)
        )

def main():
    mcp.run()
    
if __name__ == "__main__":
    main()

# MCP Server Issues and Fixes

This directory contains documentation of issues encountered during the development of the Filesystem MCP server and their solutions.

## Issues Documented

- [StreamedRunResult Output Error](streaming_output_error.md) - Fixed an issue where accessing `output` attribute on StreamedRunResult after delta streaming caused AttributeError

## Key Insights

1. When using `stream_text(delta=True)`, the StreamedRunResult object does not build a complete string internally, so `result.output` remains unset

2. To preserve the complete output while using efficient delta streaming, we need to manually concatenate the delta chunks

3. Pydantic-AI provides multiple streaming methods with different behaviors that need to be understood for proper use:
   - `stream()` - Streams raw response as an async iterable
   - `stream_text()` - Streams text result as string
   - `stream_text(delta=True)` - Streams text deltas for maximum efficiency 
   - `stream_structured()` - Streams structured data in partial format
   - `get_output()` - Retrieves the full output after streaming (not compatible with delta=True)
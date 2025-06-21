# PydanticAI `iter()` Method Research

## Overview

The `iter()` method in PydanticAI provides low-level access to the agent's execution graph, allowing us to manually control the flow of execution and inspect each node as it runs. This is precisely what we need to solve our issue with Claude's tool calls and streaming, as it will let us continue processing the stream even after a tool call is detected.

## How `iter()` Works

The `iter()` method returns an `AgentRun` object that is both an async context manager and an async iterator. Here's what happens:

1. It builds the agent's internal graph (system prompts, tools, result schemas).
2. It returns an `AgentRun` object that can be used to iterate through the nodes of the graph as they execute.
3. Each iteration yields a node that represents a step in the agent's execution flow.

## Key Node Types

PydanticAI provides helper methods to identify different node types:

- `is_model_request_node(node)`: Checks if the node is a `ModelRequestNode` (a request to the LLM)
- `is_call_tools_node(node)`: Checks if the node is a `CallToolsNode` (processing a tool call)
- `is_user_prompt_node(node)`: Checks if the node is a `UserPromptNode` (user input)
- `is_end_node(node)`: Checks if the node is an `End` node (signals end of execution)

## Using `iter()` for Manual Control

There are two ways to use the `iter()` method:

### 1. Async For Loop

```python
async with agent.iter(user_input) as agent_run:
    async for node in agent_run:
        # Process each node type differently
        if agent.is_model_request_node(node):
            # A request to the model
            pass
        elif agent.is_call_tools_node(node):
            # A node that processes tool calls
            tool_response = node.model_response
            # Extract tool calls, process them
            pass
```

### 2. Manual Next Method

For more control, we can use the `next()` method to manually drive the execution:

```python
async with agent.iter(user_input) as agent_run:
    next_node = agent_run.next_node  # First node
    while not agent.is_end_node(next_node):
        next_node = await agent_run.next(next_node)  # Run the node and get the next one
        # Process node based on its type
```

## Solving the Claude Streaming Issue

For our specific issue with Claude not providing text after tool calls in streaming mode, we can use `iter()` to:

1. Identify when a tool call is made (`is_call_tools_node`)
2. Execute the tool call
3. Continue the execution flow instead of breaking out immediately
4. Handle any text responses that come after the tool call

This approach bypasses the built-in early exit of `run_stream()` and gives us full control over when to terminate the stream processing.

## Implementing a Solution

The solution will need to:

1. Use `agent.iter()` to iterate through nodes
2. For `CallToolsNode` nodes:
   - Extract and process tool calls
   - Continue iteration to potentially receive text responses after tool calls
3. For `ModelRequestNode` nodes:
   - Process any streaming text responses
4. Maintain a buffer to collect all parts of the response
5. Only terminate when an `End` node is reached

## Implementation Considerations

- We'll need to manually manage the output format to return both tool results and text responses
- We might need to deal with state management to track tool calls and their results
- We should handle both streaming and non-streaming output options
- The solution needs to be compatible with all LLM providers but specifically optimized for Claude
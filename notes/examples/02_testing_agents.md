# Testing Agents in PydanticAI

## Agent Testing Approaches

Testing agent behavior in PydanticAI applications involves several strategies:

1. **Unit Testing**: Testing individual agent components (tools, output validators)
2. **Integration Testing**: Testing the agent with its dependencies
3. **End-to-End Testing**: Testing the full system with real or simulated user interactions

## PydanticAI Testing Features

PydanticAI provides several features to facilitate testing:

1. **Dependency Injection**: Makes it easier to mock external dependencies
2. **Test Models**: `TestModel` allows controlling LLM responses in tests
3. **Message History Management**: Simulating conversations with predefined history

## Agent Test Script Example

Based on the `get_agent_instructions` output, here's how agent testing is typically set up:

```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from dotenv import load_dotenv
import os

load_dotenv()

import logfire
logfire.configure(token=os.getenv("LOGFIRE_API_KEY"))
logfire.instrument_openai()

# Set up OpenRouter based model
API_KEY = os.getenv('OPENROUTER_API_KEY')
model = OpenAIModel(
    'anthropic/claude-3.7-sonnet',
    provider=OpenAIProvider(
        base_url='https://openrouter.ai/api/v1', 
        api_key=API_KEY
    ),
)

# MCP Environment variables
env = {
    "SOME_API_KEY": os.getenv("SOME_API_KEY"),
    "ANOTHER_API_KEY": os.getenv("ANOTHER_API_KEY"),
}

mcp_servers = [
    MCPServerStdio('python', ['data/projects/xsus/mcp_server.py'], env=env),
]

from datetime import datetime, timezone

# Set up Agent with Server
agent_name = "pydantic_tester"
def load_agent_prompt(agent:str):
    """Loads given agent replacing `time_now` var with current time"""
    print(f"Loading {agent}")
    time_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with open("data/projects/xsus/agents/" + f"{agent}.md", "r") as f:
        agent_prompt = f.read()
    agent_prompt = agent_prompt.replace('{time_now}', time_now)
    return agent_prompt

# Load up the agent system prompt
agent_prompt = load_agent_prompt(agent_name)
print(agent_prompt)
agent = Agent(model, mcp_servers=mcp_servers, system_prompt=agent_prompt)

import random, traceback

async def main():
    """CLI testing in a conversation with the agent"""
    async with agent.run_mcp_servers(): 

        message_history = []
        result = None

        while True:
            if result:
                print(f"\n{result.output}")
            user_input = input("\n> ")
            result = None
            err = None
            for i in range(0, 3):
                try:
                    result = await agent.run(
                        user_input, 
                        message_history=message_history
                    )
                    break
                except Exception as e:
                    err = e
                    traceback.print_exc()
                    if len(message_history) > 2:
                        message_history.pop(0)
                    await asyncio.sleep(2)
            if result is None:
                print(f"\nError {err}. Try again...\n")
                continue
            message_history.extend(result.new_messages())
            while len(message_history) > 6:
                message_history.pop(0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Testing Approaches in XSUS

The XSUS project includes several approaches to testing:

1. **Agent Scripts**: Standalone scripts for testing agent behavior
2. **End-to-End Tests**: Testing the full system including the web interface
3. **Debug Endpoints**: Special endpoints for debugging agent behavior

## Automated Testing with Test Prompts

A common pattern is to use a set of predefined test prompts stored in a JSON file:

```python
import json

# Load test prompts
with open("prompts.json", "r") as f:
    test_prompts = json.load(f)

async def run_automated_tests(agent):
    """Run through a set of predefined test prompts"""
    async with agent.run_mcp_servers():
        for test_case in test_prompts:
            prompt = test_case["prompt"]
            expected_pattern = test_case.get("expected_pattern")
            
            print(f"\nTesting: {prompt}")
            try:
                result = await agent.run(prompt)
                print(f"Response: {result.output[:100]}...")
                
                # Optional validation
                if expected_pattern and re.search(expected_pattern, result.output):
                    print("✅ Test passed")
                elif expected_pattern:
                    print("❌ Test failed - pattern not found")
            except Exception as e:
                print(f"❌ Test error: {str(e)}")
```

## Common Testing Challenges

1. **Determinism**: LLM responses may vary even with the same prompt
2. **Environment Dependencies**: Tests that depend on external APIs or services
3. **MCP Server Management**: Ensuring proper startup and cleanup of MCP servers
4. **Error Handling**: Recovering from errors during testing
5. **Context Length**: Managing message history to prevent exceeding context limits
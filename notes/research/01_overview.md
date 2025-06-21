# PydanticAI Overview

## What is PydanticAI?

PydanticAI is a Python agent framework designed to simplify building production-grade applications with Generative AI. It was created by the team behind Pydantic, which is widely used for data validation in Python.

The library aims to bring a "FastAPI feeling" to GenAI app development - offering an intuitive, type-safe, and structured approach to working with large language models.

## Key Features

1. **Model-agnostic**: Supports various LLM providers including OpenAI, Anthropic, Gemini, Deepseek, Ollama, Groq, Cohere, and Mistral, with a simple interface to add support for other models.

2. **Pydantic Integration**: Uses Pydantic for data validation and structured responses, ensuring consistency across runs.

3. **Type-safety**: Designed for comprehensive type checking, making it easier to catch errors during development.

4. **Python-centric Design**: Leverages familiar Python control flow and composition patterns.

5. **Dependency Injection**: Offers an optional dependency injection system for providing data and services to agent components.

6. **Streamed Responses**: Supports streaming LLM responses with immediate validation.

7. **Graph Support**: Provides powerful graph definition using Python typing hints through Pydantic Graph.

8. **MCP Support**: Implements the Model Context Protocol (MCP) for standardized communication between AI applications.

## Framework Components

1. **Agent**: The core component that manages the interaction with LLMs, tools, and structured responses.

2. **Models**: Abstractions for different LLM providers (OpenAI, Anthropic, etc.).

3. **Tools**: Functions that the LLM can call during execution.

4. **MCP**: Client and server implementations for the Model Context Protocol.

5. **Messages**: Handling of chat history and message context.

PydanticAI is designed to be modular and extensible, allowing developers to build complex AI applications while maintaining code quality and type safety.

## Documentation Resources

The official documentation is available at [ai.pydantic.dev](https://ai.pydantic.dev/) and the source code is hosted on GitHub at [github.com/pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai).

The documentation is also available in the "llms.txt" format, a specialized Markdown format designed for large language models.
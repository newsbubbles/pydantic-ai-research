# Models and Providers in PydanticAI

## Model Architecture

PydanticAI abstracts LLM interactions through a two-level architecture:

1. **Models**: Classes that define how to interact with specific LLM architectures
2. **Providers**: Classes that define how to connect to specific LLM providers

This separation allows for flexibility in how models are accessed and configured.

## Supported Models

PydanticAI supports a wide range of models:

1. **OpenAI**: GPT-3.5, GPT-4, GPT-4o
2. **Anthropic**: Claude models (Haiku, Sonnet, Opus)
3. **Google**: Gemini models
4. **Mistral**: Mistral models
5. **Others**: Cohere, Groq, Bedrock, etc.

## Model Configuration

Here's how models are typically configured:

```python
# OpenAI model with default provider
from pydantic_ai.models.openai import OpenAIModel
model = OpenAIModel("gpt-4o")

# OpenAI model with custom provider (e.g., OpenRouter)
from pydantic_ai.providers.openai import OpenAIProvider
model = OpenAIModel(
    'anthropic/claude-3.7-sonnet',
    provider=OpenAIProvider(
        base_url='https://openrouter.ai/api/v1',
        api_key=OPENROUTER_API_KEY
    )
)

# Anthropic model
from pydantic_ai.models.anthropic import AnthropicModel
model = AnthropicModel("claude-3-opus-20240229")

# Gemini model
from pydantic_ai.models.gemini import GeminiModel
model = GeminiModel("gemini-1.5-pro")
```

## Models in XSUS

The XSUS project primarily uses Anthropic Claude models via OpenRouter:

```python
# Set up model using OpenRouter or fallback to OpenAI
if OPENROUTER_API_KEY:
    provider = OpenAIProvider(
        base_url='https://openrouter.ai/api/v1',
        api_key=OPENROUTER_API_KEY
    )
    logger.info("Using OpenRouter as provider")
else:
    provider = OpenAIProvider(api_key=OPENAI_API_KEY)
    logger.info("Using OpenAI as provider")

# Default to Claude 3.7 Sonnet as our target model
model = OpenAIModel(
    'anthropic/claude-3.7-sonnet',
    provider=provider
)
```

Notably, XSUS uses the OpenAI provider with OpenRouter as the base URL to access Anthropic Claude models. This approach provides flexibility to switch between providers while maintaining the same code structure.

## Provider Selection Factors

1. **API Compatibility**: OpenRouter provides an OpenAI-compatible API
2. **Model Access**: Access to Anthropic Claude models through OpenRouter
3. **Cost Management**: Potentially better pricing through OpenRouter
4. **Fallback Support**: Ability to fall back to OpenAI if needed

## Model Parameters

Models can be configured with various parameters:

```python
model = OpenAIModel(
    "gpt-4o",
    temperature=0.7,  # Controls randomness
    max_tokens=2000,  # Maximum response length
    top_p=1.0,        # Nucleus sampling parameter
    timeout=60.0      # Request timeout in seconds
)
```

## Common Model Issues

1. **API Key Management**: Ensuring API keys are properly secured
2. **Rate Limiting**: Handling rate limits from providers
3. **Cost Control**: Managing usage to control costs
4. **Timeout Handling**: Dealing with slow responses or timeouts
5. **Error Recovery**: Recovering from API errors

## Model Selection Strategy

For XSUS, the model selection strategy appears to be:

1. **Primary**: Claude 3.7 Sonnet via OpenRouter
2. **Fallback**: OpenAI models if OpenRouter is unavailable

This strategy provides a balance of cost, performance, and reliability.
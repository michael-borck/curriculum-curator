# 14. LiteLLM for Unified LLM Abstraction

Date: 2025-11-29

## Status

Accepted

## Context

The current LLM integration has several issues:

1. **Multiple service files** with overlapping functionality:
   - `llm_service.py` - main service with OpenAI/Anthropic
   - `llm_service_enhanced.py` - adds Ollama, streaming
   - `advanced_llm_service.py` - educational AI features

2. **Direct SDK imports** causing maintenance burden:
   - Each provider requires separate import handling
   - Try/except blocks for optional dependencies
   - Type checking issues with optional modules (93+ basedpyright errors)
   - Different response formats per provider

3. **Duplicated provider switching logic**:
   ```python
   if provider == "openai":
       client = openai.AsyncOpenAI(...)
       response = await client.chat.completions.create(...)
   elif provider == "anthropic":
       client = anthropic.AsyncAnthropic(...)
       response = await client.messages.create(...)
   # ... repeated in multiple files
   ```

4. **Hard to add new providers** - requires touching multiple files

5. **Inconsistent streaming implementations** across providers

## Decision

We will adopt **LiteLLM** as our unified LLM abstraction layer.

LiteLLM provides:
- Single API for 100+ LLM providers (OpenAI, Anthropic, Ollama, Gemini, etc.)
- OpenAI-compatible interface for all providers
- Built-in streaming support
- BYOK (Bring Your Own Key) support
- Proper async support
- Well-maintained type stubs

### New Architecture

```
┌─────────────────────────────────────────────────┐
│                  Application                     │
├─────────────────────────────────────────────────┤
│              LLMService (unified)                │
│  - generate_content()                           │
│  - generate_structured_content()                │
│  - stream_content()                             │
├─────────────────────────────────────────────────┤
│                   LiteLLM                        │
│  - acompletion() / completion()                 │
│  - Handles all provider differences             │
├─────────────────────────────────────────────────┤
│  OpenAI │ Anthropic │ Ollama │ Gemini │ ...    │
└─────────────────────────────────────────────────┘
```

### Usage Example

```python
from litellm import acompletion

# OpenAI
response = await acompletion(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    api_key=user_openai_key,  # BYOK
)

# Anthropic (same interface!)
response = await acompletion(
    model="claude-3-opus-20240229",
    messages=[{"role": "user", "content": prompt}],
    api_key=user_anthropic_key,
)

# Ollama/Local (same interface!)
response = await acompletion(
    model="ollama/llama2",
    messages=[{"role": "user", "content": prompt}],
    api_base="http://localhost:11434",
)
```

## Consequences

### Positive

- **Simplified codebase**: Remove 3 service files, replace with 1
- **Fewer type errors**: LiteLLM has proper type stubs
- **Easier provider additions**: Just change model string
- **Consistent streaming**: Same interface for all providers
- **BYOK support built-in**: Users can use their own API keys
- **Future-proof**: New providers added by LiteLLM maintainers
- **Better error handling**: Unified exception types
- **Cost tracking**: Built-in token counting and cost estimation

### Negative

- **New dependency**: Adds `litellm` package
- **Abstraction layer**: Slightly less control over raw API calls
- **Version coupling**: Dependent on LiteLLM releases for new model support
- **Learning curve**: Team needs to learn LiteLLM patterns

### Neutral

- **Migration effort**: One-time refactor of existing services
- **Configuration changes**: Model names use LiteLLM format (e.g., `ollama/llama2`)
- **Testing**: May need to mock LiteLLM instead of individual SDKs

## Alternatives Considered

### OpenRouter

- Single API key for all providers
- **Rejected**: Vendor lock-in, no local/Ollama support, less flexibility for BYOK

### Custom Factory Pattern

- Build our own provider abstraction
- **Rejected**: Significant maintenance burden, reinventing the wheel

### Keep Current Approach

- Continue with direct SDK imports
- **Rejected**: Too many type errors, code duplication, hard to maintain

### Instructor Library

- Great for structured output with Pydantic
- **Considered for future**: Could layer on top of LiteLLM for structured generation

## Implementation Notes

### Phase 1: Core Migration

1. Add `litellm` to dependencies:
   ```toml
   [project.dependencies]
   litellm = "^1.0"
   ```

2. Create unified `LLMService`:
   ```python
   # app/services/llm_service.py
   from litellm import acompletion, atext_completion
   
   class LLMService:
       async def generate_content(
           self,
           prompt: str,
           model: str = "gpt-3.5-turbo",
           api_key: str | None = None,
           **kwargs
       ) -> str:
           response = await acompletion(
               model=model,
               messages=[{"role": "user", "content": prompt}],
               api_key=api_key,
               **kwargs
           )
           return response.choices[0].message.content
   ```

3. Remove old service files:
   - `llm_service_enhanced.py`
   - `advanced_llm_service.py`

4. Update imports throughout codebase

### Phase 2: Enhanced Features

1. Add streaming support using `acompletion(stream=True)`
2. Implement structured output with response parsing
3. Add cost tracking using LiteLLM's token counting
4. Configure fallback models

### Model Name Mapping

| Current | LiteLLM Format |
|---------|----------------|
| `gpt-4` | `gpt-4` |
| `claude-3-opus` | `claude-3-opus-20240229` |
| `llama2` (Ollama) | `ollama/llama2` |
| `gemini-pro` | `gemini/gemini-pro` |

### Environment Variables

LiteLLM respects standard env vars:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`

Or pass `api_key` directly for BYOK.

## References

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Supported Providers](https://docs.litellm.ai/docs/providers)
- [ADR-003](003-plugin-architecture.md) - Plugin system that may use LLM
- [ADR-004](004-teaching-philosophy-system.md) - Teaching styles influence LLM prompts

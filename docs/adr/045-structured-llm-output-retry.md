# 45. Structured LLM Output with Retry Loop

Date: 2026-02-22

## Status

Accepted

## Context

Several features require structured JSON from LLMs: Quick Scaffold generates a complete unit structure, Fill Gaps detects missing components, and prompt templates produce typed results. The LLM must return JSON that validates against a specific Pydantic model.

LLMs — especially smaller local models via Ollama — frequently produce invalid JSON (trailing commas, markdown fencing, missing fields, wrong types). A single-shot approach would fail too often to be usable. The system needs a reliable way to get valid structured output from any provider, including models that don't support native JSON mode.

## Decision

Implement a multi-attempt conversation-based retry loop that communicates the expected schema via prompt injection, cleans up common formatting issues, and feeds validation errors back to the model as correction prompts.

### Schema Communication

The Pydantic model's JSON schema (via `.model_json_schema()`) is serialised and injected directly into the prompt:

```
IMPORTANT: You must respond with valid JSON that matches this exact schema:
{json_schema}

Provide ONLY the JSON object, no additional text or markdown formatting.
```

For OpenAI GPT-4 models, `response_format: {"type": "json_object"}` is additionally set to enable native JSON mode. All other providers (Anthropic, Gemini, Ollama) rely on prompt engineering alone.

### Retry Mechanism

Up to 3 attempts (configurable via `max_retries`), with:

1. **Temperature decay:** Each retry reduces temperature by 0.1 (floor at 0.3). Default sequence: 0.7 → 0.6 → 0.5. Lower temperature produces more deterministic output, increasing the chance of valid JSON.

2. **Markdown cleanup:** Before parsing, strip `` ```json `` / `` ``` `` fencing that models commonly add despite being told not to.

3. **Multi-turn correction:** On failure, the error message is appended as a new user message in the conversation (not a fresh prompt), so the model can see its previous attempt and the specific error:
   - `JSONDecodeError` → "Your response was not valid JSON. Error: {e}. Please provide valid JSON only."
   - `ValidationError` → "Your JSON didn't match the required schema. Errors: {e.json()}. Please fix."
   - Other exceptions → immediate failure, no retry

### Return Type

`(validated_model, None)` on success, `(None, error_string)` on exhaustion.

## Consequences

### Positive
- Provider-agnostic — works with any LLM, including small local Ollama models that struggle with JSON
- Self-correcting — models often fix their output when shown the specific validation error
- Temperature decay biases retries toward more reliable output
- No external dependencies — uses only Pydantic and the existing LLM service

### Negative
- Retries cost additional tokens and latency (up to 3x in worst case)
- The JSON schema in the prompt consumes context window, which matters for small models
- Prompt-based schema enforcement is less reliable than native structured output (only available for OpenAI GPT-4)
- Multi-turn correction assumes the model can reason about its errors — very small models may not improve on retry

### Neutral
- The 3-attempt default is a pragmatic limit — empirically, most recoverable failures resolve by attempt 2
- Temperature floor of 0.3 prevents fully deterministic output, preserving some variety in retries

## Alternatives Considered

### Instructor / Outlines Library
- Libraries that patch LLM clients with automatic structured output, retry, and validation
- Rejected: adds a dependency that may conflict with our multi-provider abstraction (LiteLLM); our retry needs are simple enough to implement directly; Instructor's Ollama support was limited when this was built

### Function Calling / Tool Use
- Use the model's native function calling API to enforce output structure
- Rejected: not universally supported (Ollama models vary, Anthropic's tool use has different semantics); function calling doesn't guarantee valid JSON for all models

### Post-Processing with a Second LLM Call
- Send invalid output to a separate "fixer" model
- Rejected: doubles cost and latency; the multi-turn approach achieves the same effect by letting the original model correct itself

### Fail Fast (No Retry)
- Return error immediately on invalid JSON
- Rejected: unacceptable UX — scaffold and fill-gap are high-value features that users expect to work; transient JSON errors from capable models should not surface as failures

## Implementation Notes

- System prompt: `"You are an expert curriculum designer. Always respond with valid JSON."`
- Markdown cleanup regex handles ````json`, bare ```` ``` ````, and mixed fencing
- The conversation history accumulates across retries, so attempt 3 sees: system → user prompt → assistant attempt 1 → user error 1 → assistant attempt 2 → user error 2
- `generate_with_template()` delegates to `generate_structured_content()` when a `response_model` is provided

## References

- `backend/app/services/llm_service.py` — `generate_structured_content()`
- [ADR-014: LiteLLM Unified LLM Abstraction](014-litellm-unified-llm-abstraction.md)
- [ADR-032: AI Assistance Levels](032-ai-assistance-levels.md)

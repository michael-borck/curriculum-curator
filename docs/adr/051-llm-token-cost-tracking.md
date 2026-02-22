# 51. LLM Token Usage and Cost Tracking

Date: 2026-02-23

## Status

Accepted

## Context

The app supports multiple LLM providers (OpenAI, Anthropic, Gemini, Ollama) with a bring-your-own-key model. Users need visibility into their AI usage — both for personal cost awareness and for administrators monitoring system-wide consumption. Token counts and costs vary dramatically across providers and models.

## Decision

Implement a dual-model tracking system: fine-grained per-generation history for content traceability, and aggregated token usage logs for cost reporting.

### Model 1 — Generation History (Content Traceability)

The `GenerationHistory` model records every LLM call at the content level:

- **Identity:** `unit_id`, `content_id` (optional), `user_id`
- **Call details:** `generation_type` (content_creation, content_enhancement, ulo_generation, quiz_generation, summary_generation, chat_response), `llm_provider`, `model_used`
- **Full text:** `prompt_used` (complete prompt), `generated_content` (complete output), `input_context` (JSON)
- **Metrics:** `token_usage` (JSON: `{input_tokens, output_tokens}`), `execution_time_ms`, `generation_settings` (JSON: temperature, max_tokens, etc.)
- **Lifecycle:** `usage_status` (generated → edited → used / discarded), `user_rating` (JSON)

This enables: "show me what AI generated for this material", "what prompt produced this output", "how much did this generation cost".

### Model 2 — Token Usage Log (Cost Reporting)

The `TokenUsageLog` model aggregates usage for billing and analytics:

- **Fields:** `user_id`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `provider`, `model`, `cost_estimate` (float), `feature` (which app feature), `created_at` (indexed)
- **API:** `GET /llm-config/usage/stats?days=30` (per-user), `GET /llm-config/usage/stats/all?days=30` (admin)
- **Aggregation:** totals, cost sums, breakdowns by provider and by model

### Token Estimation

`estimate_tokens(text, model)`: Uses `tiktoken` (OpenAI's tokeniser) when available, falls back to `len(text) // 4` (the ~4 chars/token heuristic). The fallback ensures the feature works without `tiktoken` installed — relevant for minimal Ollama-only deployments.

### Cost Estimation

`estimate_cost(input_tokens, output_tokens, model)`: First tries LiteLLM's `completion_cost()`. Falls back to a hardcoded pricing table (per 1K tokens):

| Model | Input | Output |
|-------|-------|--------|
| gpt-4 | $0.030 | $0.060 |
| gpt-4-turbo | $0.010 | $0.030 |
| gpt-3.5-turbo | $0.0005 | $0.0015 |
| claude-3-opus | $0.015 | $0.075 |
| claude-3-sonnet | $0.003 | $0.015 |

Model matching uses substring search with gpt-4 as the default fallback. Local Ollama models would match the default and get a (meaningless but non-zero) cost estimate.

## Consequences

### Positive
- Full prompt/output history enables debugging, auditing, and quality improvement
- Dual models separate concerns: traceability (per-generation) vs reporting (aggregated)
- Fallback strategies (char count for tokens, hardcoded table for costs) mean the feature works without optional dependencies
- Per-user stats enable BYOK cost awareness — users can see how much their API keys are being used

### Negative
- The hardcoded pricing table will drift as providers change prices — requires manual updates
- `tiktoken` fallback (`len // 4`) is a rough approximation — overestimates for code, underestimates for CJK text
- Storing full prompt and output text in `GenerationHistory` significantly increases database size over time
- The generation pipeline does not yet automatically write to these tables — call sites must explicitly record usage

### Neutral
- `TokenUsageLog.cost_estimate` is nullable — local Ollama usage can be tracked by tokens without a meaningful cost
- Generation history tracks `usage_status` lifecycle but status transitions are manual (the user or UI must update status)
- Substring model matching (`"gpt-4" in model.lower()`) is fragile for future model names but works for current naming conventions

## Alternatives Considered

### LiteLLM-Only Tracking
- Rely entirely on LiteLLM's built-in usage callbacks and cost tracking
- Rejected: LiteLLM's tracking is per-call, not aggregated; doesn't provide content-level traceability; may not capture Ollama usage

### Single Unified Table
- One table for both per-generation detail and aggregate stats
- Rejected: the access patterns are fundamentally different — generation history is queried by unit/content, usage stats are queried by user/date range; combining them would compromise query performance and schema clarity

### No Cost Tracking for Local Models
- Skip token/cost estimation for Ollama entirely
- Rejected: users running local models still benefit from knowing token counts (helps understand context window usage and generation size)

### External Analytics Service
- Send usage data to an external monitoring service (Datadog, PostHog, etc.)
- Rejected: contradicts the privacy-first, no-telemetry architecture (ADR-037); all data must stay local

## Implementation Notes

- `GenerationHistory` model in `backend/app/models/generation_history.py`
- `TokenUsageLog` model in `backend/app/models/llm_config.py`
- Token/cost utilities in `backend/app/services/llm_service.py`: `estimate_tokens()`, `estimate_cost()`, `get_token_stats()`
- Stats endpoints in `backend/app/api/routes/llm_config.py`
- `total_tokens` is a computed property on `GenerationHistory`: `input_tokens + output_tokens` from the JSON blob

## References

- [ADR-014: LiteLLM Unified LLM Abstraction](014-litellm-unified-llm-abstraction.md)
- [ADR-037: Privacy-First, BYOK Architecture](037-privacy-first-byok-architecture.md)
- `backend/app/models/generation_history.py`
- `backend/app/models/llm_config.py`
- `backend/app/services/llm_service.py`

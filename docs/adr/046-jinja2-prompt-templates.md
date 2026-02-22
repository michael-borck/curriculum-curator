# 46. Jinja2 Prompt Template System

Date: 2026-02-22

## Status

Accepted

## Context

AI content generation requires complex, context-sensitive prompts that vary by content type, pedagogy, and unit state. Hardcoded f-strings are fragile and hard to customise. Users also want to create, version, and share their own prompt templates — a lecturer who writes a great quiz prompt should be able to reuse it across units and share it with colleagues.

The template engine needs to support conditionals (different instructions per pedagogy), loops (iterating over existing ULOs), and filters (joining lists) — more than simple variable substitution.

## Decision

Use Jinja2 as the template engine for all LLM prompts, with a two-layer architecture:

### Layer 1 — In-Memory Template Library

A `PromptTemplate` class wraps `jinja2.Environment.from_string()` with:
- **Automatic variable extraction** from the Jinja2 AST via `jinja2.meta.find_undeclared_variables()` — no need to manually declare variables
- **Strict rendering** — raises `ValueError` listing missing variables rather than producing incomplete prompts
- **Preview mode** — substitutes `<varname>` placeholders for missing variables, useful in the template editor UI

A `PromptTemplateLibrary` provides factory methods for built-in templates:
- `unit_structure_generation()` — 14 variables, includes conditional pedagogy blocks (`{% if pedagogy_approach == 'flipped' %}`)
- `learning_outcomes_refinement()` — iterates existing outcomes with `{% for outcome in current_outcomes %}`
- `lecture_content_generation()` — pedagogy-conditional instruction blocks
- `quiz_generation()` — uses `{{ bloom_levels | join(', ') }}` filter
- `assessment_rubric_generation()`, `case_study_generation()`

### Layer 2 — Database-Persisted Templates

A `PromptTemplate` SQLAlchemy model stores user-created and system templates with:
- **Ownership:** `owner_id` (nullable — null means system template), `is_system` flag (prevents deletion), `is_public` flag (sharing)
- **Versioning:** `parent_id` self-reference + `version` integer — `create_version()` forks a new record
- **Usage tracking:** `usage_count` + `last_used` timestamp, incremented via `increment_usage()`
- **Metadata:** `type` enum (unit_structure, lecture, quiz, rubric, case_study, tutorial, lab, assignment, custom), `status` (active/draft/archived), `tags` (JSON array), `model_preferences` (JSON object for model-specific settings), `example_output`
- **Content:** `template_content` (the Jinja2 string), `variables` (JSON list extracted at creation)

## Consequences

### Positive
- Jinja2 handles conditionals, loops, and filters — prompts can adapt to pedagogy, content type, and existing unit context
- Automatic variable extraction means templates are self-documenting — the UI can show which fields are required
- User-owned templates with versioning enable iterative prompt improvement
- System templates provide good defaults; users can fork and customise

### Negative
- Jinja2 templates without sandboxing could theoretically execute arbitrary code via template injection — acceptable since templates are authored by authenticated users, not end-user input
- Two layers share the `PromptTemplate` name but are independent classes — potential confusion for developers
- The wiring between DB-stored templates and the in-memory rendering engine is not yet complete — currently, built-in templates use Layer 1 directly while user templates are stored in Layer 2

### Neutral
- Template variables are stored redundantly (extracted at creation and stored as JSON) for UI display without re-parsing
- Model preferences are advisory — the system uses them to suggest a provider but doesn't enforce it

## Alternatives Considered

### Python f-strings
- Simple, no dependencies, familiar
- Rejected: no conditionals, no loops, no filters — pedagogy-conditional blocks would require nested if/else in Python code, making prompts unreadable and uneditable by non-developers

### Python `string.Template`
- Safe substitution with `$variable` syntax
- Rejected: even simpler than f-strings — no conditionals or loops at all; insufficient for the complexity of curriculum generation prompts

### LLM Orchestration Framework (LangChain, etc.)
- Full prompt management with chains, memory, and template support
- Rejected: heavy dependency for what is fundamentally a template rendering problem; our needs are met by Jinja2 alone without the abstraction overhead

### Mako Templates
- More Pythonic template syntax, compiled to Python bytecode
- Rejected: Jinja2 is the de facto standard in Python web development (used by Flask, FastAPI docs, Ansible); better community knowledge and tooling

## Implementation Notes

- Template rendering: `jinja2.Environment().from_string(template).render(**kwargs)`
- Variable extraction: `jinja2.meta.find_undeclared_variables(env.parse(template))` — returns a set of variable names the template expects
- The `prepare_unit_structure_prompt()` utility injects `json_schema` (as `json.dumps(schema, indent=2)`) into the template context for structured output (see ADR-045)
- DB model `TemplateType` enum: `unit_structure`, `learning_outcomes`, `lecture`, `quiz`, `rubric`, `case_study`, `tutorial`, `lab`, `assignment`, `custom`

## References

- `backend/app/services/prompt_templates.py` — in-memory template library
- `backend/app/models/prompt_template.py` — database model
- [ADR-045: Structured LLM Output with Retry](045-structured-llm-output-retry.md)
- [ADR-004: Teaching Philosophy System](004-teaching-philosophy-system.md)

# ADR-058: Prompt Template Library

Date: 2026-02-25

## Status

Accepted

## Context

The AI assistant's quick actions were hardcoded strings in the React component — impossible to customise, extend, or share between users. A complete `PromptTemplate` SQLAlchemy model already existed in the codebase but was never registered with `Base.metadata` or exposed via API routes.

We need a system where:

1. Admins can provide default ("system") prompts that all users see
2. Users can create their own custom prompts
3. Users can share prompts with others (read-only)
4. Users can hide prompts they don't use without deleting them
5. Templates support variables (e.g. `{{unit_level}}`, `{{content}}`) that the frontend renders as input fields before sending

## Decision

### Three-tier permission model

| Tier | Created by | See | Edit | Hide | Share | Copy |
|------|-----------|-----|------|------|-------|------|
| **System** | Seed script / admin | All users | No | Yes | N/A | Yes |
| **Custom** | User | Owner | Owner | Yes | Mark `is_public` | Yes |
| **Public** | Another user (shared) | All users | No | Yes | N/A | Yes |

"System" refers to admin-managed teaching prompts, not LLM system prompts.

### Visibility toggle

Per-user hide/unhide is stored as `hidden_prompt_template_ids` (JSON array) inside the user's `teaching_preferences` column — the same pattern used for quality/UDL metric toggles. The `GET /api/prompt-templates` endpoint filters hidden IDs by default, with `?include_hidden=true` to show all.

### Template variables

Template content uses `{{variable}}` Jinja2-style syntax. The `variables` JSON column stores metadata (name, label, default value) so the frontend can render typed input fields. A simple string-replace renderer handles interpolation — no Jinja2 dependency required.

### Seed-at-startup pattern

10 system teaching templates are seeded idempotently during app lifespan startup (same pattern as the Ollama config seed). The seed function checks by name before inserting to avoid duplicates.

### API surface

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/prompt-templates` | List visible templates |
| `GET` | `/api/prompt-templates/{id}` | Get single template |
| `POST` | `/api/prompt-templates` | Create custom template |
| `POST` | `/api/prompt-templates/{id}/copy` | Copy to own custom list |
| `PUT` | `/api/prompt-templates/{id}` | Update (owner only) |
| `DELETE` | `/api/prompt-templates/{id}` | Delete (owner only) |
| `POST` | `/api/prompt-templates/{id}/toggle-visibility` | Hide/unhide for user |
| `POST` | `/api/prompt-templates/{id}/increment-usage` | Bump usage counter |
| `POST` | `/api/prompt-templates/admin/system` | Create system template (admin) |

## Consequences

- Quick actions in the AI assistant are now data-driven, not hardcoded
- Users can build a personal prompt library tailored to their teaching style
- System templates provide sensible defaults for new users
- The `PromptTemplate` model (which was already in the codebase) is now properly registered and the table is created by `Base.metadata.create_all()`
- No migration needed — clean slate policy applies (no production users)
- Template versioning columns exist in the model but have no UI yet (future enhancement)

## Key Files

- `backend/app/models/prompt_template.py` — SQLAlchemy model (pre-existing, now registered)
- `backend/app/schemas/prompt_template.py` — Pydantic schemas
- `backend/app/api/routes/prompt_templates.py` — CRUD endpoints
- `backend/app/services/seed_prompt_templates.py` — 10 system template seeds
- `frontend/src/services/promptTemplateApi.ts` — TypeScript API client
- `frontend/src/features/ai/AIAssistant.tsx` — DB-driven quick actions + variable forms

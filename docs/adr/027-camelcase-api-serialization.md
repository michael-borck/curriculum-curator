# 27. CamelCase API Serialization Convention

Date: 2026-02-20

## Status

Accepted

## Context

The Curriculum Curator has a Python backend (snake_case convention) and a TypeScript frontend (camelCase convention). When the React frontend was introduced (ADR-016), we needed a consistent serialization strategy for the JSON API boundary.

The initial implementation used snake_case in JSON responses (matching Python), which created two problems:

1. **Frontend inconsistency** — TypeScript interfaces used camelCase internally but received snake_case from the API, requiring manual mapping or `any` types
2. **Field name mismatches** — Multiple commits (`23e21458`, `87d541b1`, `cf14733b`) fixed bugs caused by mismatched field names between frontend expectations and backend responses

JavaScript/TypeScript convention is camelCase. Most modern APIs (GitHub, Stripe, Google) use either camelCase or snake_case consistently — the key is picking one and sticking with it.

## Decision

Use **camelCase in JSON responses** while keeping **snake_case in Python code**, via Pydantic's `alias_generator`.

### Implementation

A `CamelModel` base class handles the conversion automatically:

```python
# app/schemas/base.py
from pydantic import BaseModel, ConfigDict

def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=snake_to_camel,
        populate_by_name=True,     # Accept both camelCase and snake_case input
        from_attributes=True,      # Allow from ORM models
        use_enum_values=True,
    )
```

### Behaviour

| Direction | Format | Example |
|-----------|--------|---------|
| Python code | snake_case | `user_id`, `is_active`, `model_name` |
| JSON response | camelCase | `userId`, `isActive`, `modelName` |
| JSON request | Both accepted | `userId` or `user_id` both work |
| TypeScript interface | camelCase | `userId: string` |

### Example

```python
# Backend schema
class UnitResponse(CamelModel):
    unit_code: str
    credit_points: int
    owner_id: str
```

```json
// JSON output
{
  "unitCode": "COMP101",
  "creditPoints": 6,
  "ownerId": "abc-123"
}
```

```typescript
// Frontend interface
interface Unit {
  unitCode: string;
  creditPoints: number;
  ownerId: string;
}
```

## Consequences

### Positive

- **Zero mapping code** — Frontend receives camelCase natively, no manual conversion needed
- **Convention-aligned** — Python stays PEP 8 (snake_case), TypeScript stays idiomatic (camelCase)
- **Bidirectional tolerance** — `populate_by_name=True` means the API accepts both conventions on input, reducing integration friction
- **Single source of truth** — The conversion lives in one base class, not scattered across endpoints

### Negative

- **All schemas must inherit CamelModel** — Forgetting to inherit from `CamelModel` produces snake_case output, causing subtle frontend bugs
- **OpenAPI docs show aliases** — Swagger UI shows camelCase field names, which can confuse backend developers reading the docs
- **Debugging friction** — When inspecting database queries (snake_case) alongside API responses (camelCase), developers must mentally translate

### Neutral

- **No runtime cost** — Pydantic's alias generation is computed once at class creation, not per-request
- **Migration was one-time** — All existing schemas were updated in commit `9707c55f`

## Alternatives Considered

### snake_case everywhere (Python convention)

- Frontend adapts to backend convention
- **Rejected**: Violates TypeScript conventions, requires mapping utilities on every API call, caused field mismatch bugs

### camelCase everywhere (including Python)

- Backend uses camelCase in Python code
- **Rejected**: Violates PEP 8, looks wrong in Python, confuses linters

### Manual per-field aliases

- Use Pydantic's `Field(alias="camelName")` on each field
- **Rejected**: Enormous boilerplate, easy to forget, not maintainable across 50+ schemas

### Client-side transformation library (e.g., `humps`)

- Auto-convert snake_case responses to camelCase in the Axios interceptor
- **Rejected**: Adds runtime overhead, hides the real API contract, makes debugging harder

## References

- [ADR-016: React + TypeScript Frontend](016-react-typescript-frontend.md) — Frontend convention
- [ADR-017: FastAPI REST Backend](017-fastapi-rest-backend.md) — Backend framework and Pydantic usage
- [Pydantic Model Config: alias_generator](https://docs.pydantic.dev/latest/concepts/config/#alias-generator)
- Relevant commit: `9707c55f`

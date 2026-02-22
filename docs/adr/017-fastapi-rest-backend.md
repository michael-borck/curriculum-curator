# 17. FastAPI REST Backend with JWT Authentication

Date: 2025-12-01

## Status

Accepted

## Context

With the frontend migration to React (ADR-016), the backend architecture shifted from server-rendered HTML (FastHTML) to a REST API serving a separate SPA frontend.

### Requirements

1. **API-first design**: Frontend communicates via JSON REST endpoints
2. **Stateless authentication**: No server-side sessions (supports horizontal scaling)
3. **Type safety**: Automatic validation and OpenAPI documentation
4. **Async support**: Non-blocking I/O for LLM calls and file processing
5. **Python ecosystem**: Leverage existing ML/NLP libraries

### Previous Architecture (FastHTML)

- Server-rendered HTML pages
- Session-based authentication with cookies
- HTMX for partial page updates
- Tight coupling between routing and UI

### New Requirements

- Clean API boundary for React frontend
- JWT tokens for stateless auth
- CORS support for development
- Potential for future mobile apps or third-party integrations

## Decision

Use **FastAPI** as the REST API backend with **JWT authentication**.

### Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | FastAPI >= 0.109 | Modern async Python, automatic OpenAPI |
| **Server** | Uvicorn | ASGI server with uvloop performance |
| **Validation** | Pydantic v2 | Type-safe request/response models |
| **Auth** | python-jose + passlib | JWT tokens, bcrypt password hashing |
| **Database** | SQLAlchemy 2.0 + SQLite | Async ORM, simple deployment |
| **Migrations** | Alembic | Schema versioning |
| **Rate Limiting** | SlowAPI | Request throttling |
| **LLM Integration** | LiteLLM | Unified provider interface (ADR-014) |

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    JWT Authentication                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Login: POST /api/auth/login                             │
│     Request:  { email, password }                           │
│     Response: { access_token, token_type: "bearer" }        │
│                                                              │
│  2. Authenticated Requests:                                  │
│     Header: Authorization: Bearer <access_token>            │
│                                                              │
│  3. Token Validation:                                        │
│     - Verify JWT signature (SECRET_KEY + HS256)             │
│     - Check expiration (ACCESS_TOKEN_EXPIRE_MINUTES)        │
│     - Extract user_id from payload                          │
│                                                              │
│  4. Token Refresh:                                          │
│     POST /api/auth/refresh (with valid token)               │
│     Returns new access_token                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### API Structure

```
backend/app/
├── api/
│   ├── deps.py              # Dependency injection (get_current_user, etc.)
│   └── routes/
│       ├── auth.py          # Login, register, refresh, password reset
│       ├── admin.py         # Admin-only endpoints
│       ├── units.py         # Unit CRUD
│       ├── materials.py     # Content materials
│       ├── assessments.py   # Quizzes, assignments
│       ├── llm.py           # LLM generation endpoints
│       └── content_export.py # Export (PDF, DOCX, PPTX)
├── core/
│   ├── config.py            # Pydantic settings from env
│   └── security.py          # JWT utilities, password hashing
├── models/                   # SQLAlchemy models
├── schemas/                  # Pydantic request/response schemas
├── services/                 # Business logic layer
└── main.py                   # FastAPI app, middleware, routes
```

### Security Middleware Stack

Applied in order (first to last):
1. **TrustedHostMiddleware** - Validate Host header
2. **RequestValidationMiddleware** - Size limits (10MB)
3. **SecurityHeadersMiddleware** - CSP, X-Frame-Options, etc.
4. **TrustedProxyMiddleware** - Handle X-Forwarded-For
5. **CORSMiddleware** - Allow React dev server origin

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Production restricts origins to actual deployment domain.

## Consequences

### Positive

- **Scalability**: Stateless JWT allows horizontal scaling
- **Documentation**: Automatic OpenAPI/Swagger at `/docs`
- **Type safety**: Pydantic validation catches errors early
- **Async performance**: Non-blocking LLM and file operations
- **Separation of concerns**: Clean API boundary, testable independently
- **Future flexibility**: Same API serves web, mobile, integrations

### Negative

- **Token management**: Client must handle token storage and refresh
- **CORS complexity**: Development requires proper CORS config
- **No session state**: Some features harder without server sessions
- **Two codebases**: Python backend + TypeScript frontend

### Neutral

- **API versioning**: Should consider `/api/v1/` prefix for future breaking changes
- **Token expiration**: Balance between security (short) and UX (long)
- **Error format**: Standardized JSON error responses needed

## Alternatives Considered

### Django REST Framework

- **Why rejected**: Heavier, synchronous by default, more boilerplate

### Flask + Flask-RESTful

- **Why rejected**: Less built-in validation, no native async, manual OpenAPI

### GraphQL (Strawberry/Ariadne)

- **Why rejected**: Added complexity for CRUD app; REST sufficient for current needs

### Session-based Auth (Cookies)

- **Why rejected**: Complicates CORS, harder to scale, less suitable for potential mobile apps

## Implementation Notes

### JWT Configuration

```python
# core/config.py
class Settings(BaseSettings):
    SECRET_KEY: str  # Generate with: openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

### Protected Route Pattern

```python
# api/deps.py
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user

# api/routes/units.py
@router.get("/units")
async def list_units(
    current_user: User = Depends(get_current_user)
):
    # User is authenticated
    ...
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("5/minute")  # Prevent brute force
async def login(request: Request, ...):
    ...
```

## References

- [ADR-016: React + TypeScript Frontend](016-react-typescript-frontend.md)
- [ADR-014: LiteLLM for Unified LLM Abstraction](014-litellm-unified-llm-abstraction.md)
- [ADR-010: Security Hardening](010-security-hardening.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT Best Practices (Auth0)](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

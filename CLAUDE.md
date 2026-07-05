# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

### Starting the Application
```bash
# Start backend (FastAPI + uvicorn)
./backend.sh

# Start frontend (React + Vite) - run in separate terminal
./frontend.sh
```

Both scripts handle dependency installation, environment setup, and service startup automatically.

### Build Commands
```bash
# Frontend build
cd frontend && npm run build

# Frontend preview
cd frontend && npm run preview
```

### Code Quality Commands

**IMPORTANT: Run linters and type checkers after every code change. All checks must pass with 0 errors before committing.**

```bash
# Backend linting and formatting (tools live in the uv-managed venv)
cd backend
.venv/bin/ruff check .       # Fast linting - MUST have 0 errors
.venv/bin/ruff format .      # Fast formatting
.venv/bin/basedpyright       # Type checking - MUST have 0 errors

# Frontend linting and formatting
cd frontend
npm run lint              # ESLint checking - MUST have 0 errors
npm run lint:fix          # Auto-fix ESLint issues
npm run format            # Prettier formatting
npm run format:check      # Check formatting without changes
npm run type-check        # TypeScript checking - MUST have 0 errors
```

#### Quality Gates (MANDATORY)
- **Before committing**: Run all linters and type checkers
- **Zero tolerance**: All checks must pass with 0 errors
- **Fix immediately**: Address linting issues as you write code, not after
- **Technical debt prevention**: Never ignore or suppress warnings without justification

### Testing Commands
```bash
# Backend tests with coverage (run from backend/)
cd backend
.venv/bin/pytest                   # Run all tests
.venv/bin/pytest -v                # Verbose output
.venv/bin/pytest --cov=app         # With coverage report
.venv/bin/pytest -m "not slow"     # Skip slow tests

# Run a single service test file
.venv/bin/pytest tests/test_ulo_service.py -v

# Frontend tests (Vitest + React Testing Library)
cd frontend
npm test                 # Run tests in watch mode
npm run test:coverage    # Run tests with coverage report  
npm run test:ui          # Run tests with UI interface
```

#### Backend Testing Philosophy
- **Real DB, not mocks**: Service tests use in-memory SQLite via `conftest.py` fixtures (`test_db`, `test_user`, `test_unit`, `test_unit_outline`). This catches real query bugs that mocks would miss.
- **Only mock external boundaries**: LLM API calls, SMTP, HTTP requests to third parties. Everything else (SQLAlchemy queries, model relationships, transactions) runs against the real database.
- **Test files**: One file per service (`tests/test_<service_name>.py`). All service methods are async, tests use `@pytest.mark.asyncio`.

## Terminology - Australian University Context

**IMPORTANT: This application uses Australian university terminology**

### Core Concepts
- **Unit** = Individual subject/course (e.g., "Programming 101", "Web Development")
  - A unit runs for one semester (12-13 weeks)
  - Students enroll in multiple units per semester
  - Each unit has credit points (typically 6-25 credits)

- **Course** = Degree program (e.g., "Bachelor of Computer Science")
  - NOT what this app manages
  - A course consists of many units

### USA vs Australian Terminology
- 🇺🇸 USA: Program → Course → Class
- 🇦🇺 AUS: Course → Unit → Class

### Legacy Code
- The old `/api/courses` alias endpoints have been removed. Use `/api/units`.
- The frontend keeps a `/courses` → `/units` route redirect for old bookmarks.

## Architecture Overview

**Full-stack application**: FastAPI backend + React frontend with clear API boundaries.

**Scope**: This app manages individual **Units** (subjects), NOT degree programs (Courses).

### Backend Architecture (`/backend/app/`)
- **FastAPI REST API** with JWT authentication
- **Modern Python tooling**: uv (package manager), ruff (linting/formatting), basedpyright (type checking), pytest (testing)
- **Plugin architecture** for content validation/remediation (`plugins/`)
- **LLM service integration** supporting OpenAI, Anthropic with streaming (`services/llm_service.py`)
- **Modular API routes** by domain: auth, units, content, llm (`api/routes/`)
- **SQLAlchemy + Alembic** ready (database models not yet implemented)
- **pyproject.toml** for modern dependency management

### Frontend Architecture (`/src/`)
- **TypeScript-first**: ALL components must be `.tsx` files, no `.jsx` allowed
- **Modern React tooling**: ESLint (linting), Prettier (formatting), Vitest (testing)
- **Feature-based structure**: `features/{auth,content,units}/`
- **Shared components**: `components/{Editor,Layout,Wizard}/`
- **Zustand state management** (minimal, auth only)
- **TipTap rich text editor** with table/code block support
- **Tailwind CSS** styling
- **Vite** for fast development and building

## Key Components

### LLM Integration (`backend/app/services/llm_service.py`)
- Supports multiple providers (OpenAI, Anthropic)
- Pedagogy-aware prompts (9 teaching styles)
- Streaming content generation via Server-Sent Events
- Configurable via environment variables

### Rich Text Editor (`frontend/src/components/Editor/RichTextEditor.tsx`)
- Professional TipTap-based editor
- Table support, code blocks with syntax highlighting
- Pedagogy hints based on selected teaching style

### Content Creation Flow
1. User selects pedagogy via `PedagogySelector` component
2. Content generated via `/api/llm/generate` with streaming
3. Real-time editing in `RichTextEditor`
4. Enhancement via `/api/llm/enhance`

## Important Files

### Configuration
- `backend/app/core/config.py` - Environment-based settings
- `frontend/vite.config.js` - Vite build configuration
- `frontend/tailwind.config.js` - Tailwind CSS setup

### Authentication
- `backend/app/core/security.py` - JWT utilities
- `backend/app/api/routes/auth.py` - Auth endpoints
- `frontend/src/stores/authStore.ts` - Authentication state

### API Integration
- `frontend/src/services/api.ts` - Axios client with JWT interceptors
- `frontend/src/services/apiBase.ts` - Single source of truth for the API base URL
  (relative `/api` on web; absolute localhost for the Electron `file://` renderer)
- `backend/app/api/deps.py` - FastAPI dependency injection

## Environment Variables

### Backend (.env in backend/)
```
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./data/curriculum_curator.db

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Feature Flags
ENABLE_AI_FEATURES=true
ENABLE_FILE_UPLOAD=true
DEBUG=true
```

### Frontend (.env.local in frontend/)
```
VITE_API_URL=http://localhost:8000
VITE_ENABLE_AI_FEATURES=true
```

## Development Status

### Implemented ✅
- Core API structure with JWT authentication (lockout, revocation, IP-binding)
- Full SQLAlchemy data model (33 model modules: units, materials, outcomes,
  assessments, designs, accreditation, research, etc.)
- LLM integration with streaming (OpenAI/Anthropic/Gemini/Ollama via litellm)
- Import/export pipelines (docx/pdf/pptx import; H5P/SCORM/IMSCC/QTI export)
- Git-versioned per-unit content storage
- React + TypeScript frontend with routing and rich text editing
- Pedagogy-aware content generation
- Backend test suite (~1150 pytest tests against real in-memory SQLite)
- Playwright e2e suite (21 specs)
- Electron desktop edition (bundled PyInstaller backend + pandoc/typst)
- Docker + docker-compose deployment

### Missing / In progress 🔄
- Frontend UI-level tests (stores/utils covered; pages/features largely untested)
- CI running lint/type-check/pytest/Playwright (only Docker/desktop packaging is automated)
- Encryption at rest for stored LLM API keys (currently plaintext in SQLite)
- Move JWT off localStorage to httpOnly cookies (documented in authStore.ts)

### Future Enhancements 🚀
- **Admin Dashboard**: Configuration interface for system settings
  - Password policy management (length, complexity requirements)
  - Security settings (rate limits, lockout policies)
  - User management and role assignments
  - System monitoring and security logs
- **Advanced Security**: Additional security phases (MFA, advanced monitoring)
- **Performance**: Database optimization, caching, CDN integration

## TypeScript Requirements

### Frontend Development Rules
1. **ALWAYS use TypeScript** (`.tsx` for React components, `.ts` for utilities)
2. **NEVER create `.jsx` or `.js` files** in the frontend
3. **Define interfaces** for all data structures
4. **Type all function parameters** and return values
5. **No `any` types** without explicit justification
6. **Use strict mode** - already configured in tsconfig.json

### Example Component Structure
```typescript
// ✅ CORRECT: ComponentName.tsx
interface Props {
  id: string;
  onUpdate: (data: UpdateData) => void;
}

interface State {
  loading: boolean;
  data: DataType | null;
}

export const ComponentName: React.FC<Props> = ({ id, onUpdate }) => {
  const [state, setState] = useState<State>({ loading: false, data: null });
  // ...
};

// ❌ WRONG: ComponentName.jsx or untyped parameters
```

## Common Patterns

### Adding New API Endpoints
1. Create route in `backend/app/api/routes/{domain}.py`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Implement business logic in `backend/app/services/`
4. Register route in `backend/app/main.py`

### Frontend Development Rules
1. **ALWAYS use TypeScript** (`.tsx` for React components, `.ts` for utilities)
2. **NEVER create `.jsx` or `.js` files** in the frontend
3. **Type everything**: props, state, event handlers, function returns
4. **No `any` types** without explicit justification
5. **Define interfaces** for all component props and complex data structures

### Adding New Frontend Components
1. Create as `.tsx` file in appropriate `features/` or `components/` directory
2. Define TypeScript interfaces for all props and state
3. Follow existing patterns for props and styling
4. Use Tailwind CSS classes consistently
5. Import icons from `lucide-react`
6. Type all event handlers and callbacks

### LLM Provider Integration
Extend `LLMService` class in `backend/app/services/llm_service.py` following the existing OpenAI/Anthropic pattern.

## Modern Python Tooling

This project uses modern Python tools for better performance and developer experience:

- **uv**: Ultra-fast Python package manager and resolver (replaces pip/pip-tools)
- **ruff**: Extremely fast Python linter and formatter (replaces black, flake8, isort)
- **basedpyright**: Fast type checker (replaces mypy)
- **pytest**: Testing framework with extensive configuration
- **pyproject.toml**: Modern project configuration (replaces requirements.txt, setup.py, tox.ini, etc.)

### Environment Setup
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Backend: uv manages a .venv with all tools included
cd backend
uv sync                    # Creates .venv and installs all deps (including ruff, basedpyright, pytest)

# All backend tools run from the venv:
.venv/bin/ruff check .     # Linting
.venv/bin/basedpyright     # Type checking
.venv/bin/pytest           # Tests
```

## Database Notes

**IMPORTANT: No Production Users - Clean Slate Policy**
- The production VPS currently has NO real users (only test accounts)
- Safe to drop/recreate database, modify schemas, break backwards compatibility
- NO need for migrations, deprecation warnings, or backwards-compatible changes
- When making breaking changes: just reset the database and start clean
- Reset command: `rm backend/data/curriculum_curator.db && python backend/init_db.py`

SQLAlchemy models are not implemented yet. When implementing:
- Define models in `backend/app/models/`
- Create Alembic migrations: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`
- Current setup uses SQLite for development

## Documentation

Current docs live in `docs/` — user stories, ADRs, guides, and concepts. Historical docs are preserved in git history only (no archive directory).
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
# Backend linting and formatting (modern tools)
cd backend
ruff check .              # Fast linting - MUST have 0 errors
ruff format .             # Fast formatting
basedpyright             # Type checking - MUST have 0 errors

# Legacy alternatives (if modern tools not available)
# black app/ && flake8 app/ && mypy app/

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
# Backend tests with coverage
cd backend
pytest                   # Run all tests
pytest -v                # Verbose output
pytest --cov=app         # With coverage report
pytest -m "not slow"     # Skip slow tests

# Frontend tests (Vitest + React Testing Library)
cd frontend
npm test                 # Run tests in watch mode
npm run test:coverage    # Run tests with coverage report  
npm run test:ui          # Run tests with UI interface
```

## Architecture Overview

**Full-stack application**: FastAPI backend + React frontend with clear API boundaries.

### Backend Architecture (`/backend/app/`)
- **FastAPI REST API** with JWT authentication
- **Modern Python tooling**: uv (package manager), ruff (linting/formatting), basedpyright (type checking), pytest (testing)
- **Plugin architecture** for content validation/remediation (`plugins/`)
- **LLM service integration** supporting OpenAI, Anthropic with streaming (`services/llm_service.py`)
- **Modular API routes** by domain: auth, courses, content, llm (`api/routes/`)
- **SQLAlchemy + Alembic** ready (database models not yet implemented)
- **pyproject.toml** for modern dependency management

### Frontend Architecture (`/src/`)
- **TypeScript-first**: ALL components must be `.tsx` files, no `.jsx` allowed
- **Modern React tooling**: ESLint (linting), Prettier (formatting), Vitest (testing)
- **Feature-based structure**: `features/{auth,content,courses}/`
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
- `frontend/src/stores/authStore.js` - Authentication state

### API Integration
- `frontend/src/services/api.js` - Axios client with JWT interceptors
- `backend/app/api/deps.py` - FastAPI dependency injection

## Environment Variables

### Backend (.env in backend/)
```
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./curriculum_curator.db

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
- Core API structure with authentication
- LLM integration with streaming
- React frontend with routing
- Rich text editing capabilities
- Pedagogy-aware content generation

### Missing 🔄
- Database models and relationships (SQLAlchemy models are empty)
- Plugin validators/remediators (base classes exist, implementations needed) 
- File upload processing (endpoints exist, processing incomplete)
- Test suites (pytest configured but tests not written, npm test for frontend not implemented)
- Production deployment configuration (Docker setup mentioned in README)

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

### Installation Commands
```bash
# Install modern tools globally
curl -LsSf https://astral.sh/uv/install.sh | sh  # uv
uv tool install ruff                              # ruff
uv tool install basedpyright                     # basedpyright
```

## Database Notes

SQLAlchemy models are not implemented yet. When implementing:
- Define models in `backend/app/models/`
- Create Alembic migrations: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`
- Current setup uses SQLite for development

## PRD Development Process

This project follows a 3-step PRD development process:

### Step 1: Create PRD
- Receive initial feature request
- Ask clarifying questions to understand requirements
- Generate comprehensive PRD document
- Save as `prd-[feature-name].md` in `/tasks/` directory
- **Status: ✅ Completed** - PRD created as `/docs/PRD-Curriculum-Curator.md`

### Step 2: Generate Task List
- Analyze the PRD document
- Create parent tasks (high-level)
- Wait for user confirmation ("Go")
- Generate detailed sub-tasks
- Save as `tasks-[prd-file-name].md` in `/tasks/` directory
- Include relevant files and testing strategy

### Step 3: Process Task List
- Implement one sub-task at a time
- Mark tasks as completed `[x]` after each step
- Wait for user approval before proceeding
- Update task list regularly
- Follow completion protocol and rollback procedures

**Current Status**: Ready for Step 2 - Generate task list from PRD
- We use uv controlled environment
- Remember to update the task list
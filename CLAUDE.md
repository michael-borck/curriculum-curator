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
```bash
# Backend linting and formatting
cd backend
black app/
flake8 app/
mypy app/

# Frontend linting
cd frontend
npm run lint
npm run format
```

### Testing Commands
```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

## Architecture Overview

**Full-stack application**: FastAPI backend + React frontend with clear API boundaries.

### Backend Architecture (`/backend/app/`)
- **FastAPI REST API** with JWT authentication
- **Plugin architecture** for content validation/remediation (`plugins/`)
- **LLM service integration** supporting OpenAI, Anthropic with streaming (`services/llm_service.py`)
- **Modular API routes** by domain: auth, courses, content, llm (`api/routes/`)
- **SQLAlchemy + Alembic** ready (database models not yet implemented)

### Frontend Architecture (`/src/`)
- **Feature-based structure**: `features/{auth,content,courses}/`
- **Shared components**: `components/{Editor,Layout,Wizard}/`
- **Zustand state management** (minimal, auth only)
- **TipTap rich text editor** with table/code block support
- **Tailwind CSS** styling

## Key Components

### LLM Integration (`backend/app/services/llm_service.py`)
- Supports multiple providers (OpenAI, Anthropic)
- Pedagogy-aware prompts (9 teaching styles)
- Streaming content generation via Server-Sent Events
- Configurable via environment variables

### Rich Text Editor (`frontend/src/components/Editor/RichTextEditor.jsx`)
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
- Test suites (pytest for backend, npm test for frontend not implemented)
- Production deployment configuration (Docker setup mentioned in README)

## Common Patterns

### Adding New API Endpoints
1. Create route in `backend/app/api/routes/{domain}.py`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Implement business logic in `backend/app/services/`
4. Register route in `backend/app/main.py`

### Adding New Frontend Components
1. Create in appropriate `features/` or `components/` directory
2. Follow existing patterns for props and styling
3. Use Tailwind CSS classes consistently
4. Import icons from `lucide-react`

### LLM Provider Integration
Extend `LLMService` class in `backend/app/services/llm_service.py` following the existing OpenAI/Anthropic pattern.

## Database Notes

SQLAlchemy models are not implemented yet. When implementing:
- Define models in `backend/app/models/`
- Create Alembic migrations: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`
- Current setup uses SQLite for development
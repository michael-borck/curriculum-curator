# Curriculum Curator Backend

FastAPI-based backend service for the Curriculum Curator application.

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy + SQLite (dev) / PostgreSQL (prod)
- **Authentication**: JWT tokens
- **Package Manager**: uv (ultra-fast Python package manager)
- **Linting**: ruff (fast Python linter)
- **Type Checking**: basedpyright
- **Testing**: pytest

## Quick Start

```bash
# Start the backend (handles dependencies automatically)
./backend.sh

# Or manually:
cd backend
uv sync                  # Install dependencies
uv run uvicorn app.main:app --reload --port 8000
```

## Development

### Code Quality

```bash
# Run linters (MUST pass with 0 errors before committing)
ruff check .             # Linting
ruff format .            # Formatting
basedpyright            # Type checking

# Run tests
pytest                   # All tests
pytest -v               # Verbose
pytest --cov=app        # With coverage
```

### Database

```bash
# Initialize database
python init_db.py

# Create admin user
python create_admin.py

# Setup email whitelist
python setup_whitelist.py

# Check database
python check_db.py
```

## Project Structure

```
backend/
├── app/
│   ├── api/            # API endpoints
│   │   └── routes/     # Route modules
│   ├── core/           # Core functionality (auth, security, config)
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic services
│   ├── plugins/        # Content validation/remediation plugins
│   └── main.py         # FastAPI application
├── migrations/         # Alembic database migrations
├── tests/             # Test suites
└── pyproject.toml     # Dependencies and project config
```

## Key Features

- **JWT Authentication** with email verification
- **Plugin Architecture** for content validation
- **LLM Integration** (OpenAI, Anthropic)
- **Rate Limiting** and security middleware
- **Comprehensive logging** and monitoring

## API Documentation

When running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./curriculum_curator.db

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Email (optional)
EMAIL_DEV_MODE=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Testing

```bash
# Run all tests
./run_tests.sh

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html
```

## Code Standards

See `CODING_STANDARDS.md` for detailed coding guidelines.

## Documentation

- [Email Setup](EMAIL_SETUP.md)
- [Technology Choices](TECHNOLOGY_CHOICES.md)
- [Coding Standards](CODING_STANDARDS.md)
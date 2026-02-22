# Development Guide

## Setup

### 1. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-test.txt

# Install basedpyright for type checking
pip install basedpyright
```

### 2. Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## Development Workflow

### Running the App

```bash
# Run the app
python app.py

# Or use make
make run

# Run in development mode with auto-reload
make dev
```

### Code Quality Checks

#### Type Checking with basedpyright

```bash
# Run type checking
basedpyright

# Or use the helper script
./check_types.py

# Or use make
make type-check
```

#### Linting with Ruff

```bash
# Check for linting issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Or use make
make lint
```

#### Code Formatting

```bash
# Format with black
black .

# Or use make
make format
```

#### Run All Checks

```bash
# Run lint, type-check, and tests
make check-all
```

### Testing

#### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Or use make
make test
make test-cov

# Run specific test file
pytest tests/test_app_routes.py

# Run tests matching pattern
pytest -k "teaching_style"

# Run with verbose output
pytest -v
```

#### Using the Test Runner

```bash
# Run tests with various options
./run_tests.py

# With coverage
./run_tests.py --coverage

# Run specific markers
./run_tests.py -m unit
./run_tests.py -m integration

# Run last failed
./run_tests.py --lf

# Stop on first failure
./run_tests.py -x
```

## Type Annotations

### Best Practices

1. **Import annotations from future**:
   ```python
   from __future__ import annotations
   ```

2. **Use type hints for function parameters and returns**:
   ```python
   def process_content(content: str, options: Dict[str, Any]) -> ValidationResult:
       ...
   ```

3. **Use Optional for nullable types**:
   ```python
   from typing import Optional
   
   def get_user(user_id: str) -> Optional[User]:
       ...
   ```

4. **Use Union for multiple types**:
   ```python
   from typing import Union
   
   def parse_value(value: Union[str, int, float]) -> str:
       ...
   ```

### FastHTML Type Stubs

We've created type stubs for FastHTML in `typings/fasthtml/`. These provide type hints for:
- HTML elements (Div, Span, Button, etc.)
- FastHTML app creation (`fast_app`)
- Route decorators
- Request/Response types

### Common Type Issues

1. **Missing type annotations**: Add type hints to function parameters and returns
2. **Any types**: Try to be more specific than `Any` when possible
3. **Optional vs None**: Use `Optional[T]` instead of `T | None` for clarity

## Project Structure

```
curriculum-curator/
├── app.py                 # Main FastHTML application
├── core/                  # Core business logic
│   ├── auth.py           # Authentication system
│   ├── course_manager.py # Course management
│   ├── teaching_philosophy.py # Teaching styles
│   └── plugin_manager.py # Plugin system
├── views/                 # UI components
│   ├── wizard_mode.py    # Wizard mode UI
│   └── expert_mode.py    # Expert mode UI
├── plugins/              # Plugin system
│   ├── base.py          # Base plugin classes
│   ├── validators/      # Content validators
│   └── remediators/     # Content remediators
├── tests/               # Test suite
│   ├── conftest.py      # Pytest fixtures
│   └── test_*.py        # Test files
├── typings/             # Type stubs
│   └── fasthtml/        # FastHTML type definitions
└── pyrightconfig.json   # Type checking config
```

## Makefile Commands

```bash
make help         # Show all available commands
make install      # Install dependencies
make install-dev  # Install all dependencies
make test         # Run tests
make test-cov     # Run tests with coverage
make lint         # Run linting
make type-check   # Run type checking
make format       # Format code
make clean        # Clean generated files
make check-all    # Run all checks
make run          # Run the app
make dev          # Run in dev mode
make init-db      # Initialize database
```

## VS Code Setup

The project includes VS Code settings in `.vscode/settings.json`:
- Auto-formatting on save
- Ruff linting enabled
- Type checking with Pylance/basedpyright
- Test discovery configured

## Debugging

### FastHTML Routes

To debug routes, add print statements or use Python's debugger:

```python
@rt("/test")
def get():
    import pdb; pdb.set_trace()  # Breakpoint
    return Div("Test")
```

### Type Checking Issues

Run basedpyright with verbose output:

```bash
basedpyright --verbose
```

Or check specific files:

```bash
basedpyright app.py core/teaching_philosophy.py
```

### Test Debugging

Run pytest with verbose output and stop on first failure:

```bash
pytest -vx --tb=short
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run `make check-all` to ensure quality
4. Commit with descriptive messages
5. Create a pull request

## Common Issues

### Import Errors

If you get import errors, ensure:
1. You're in the virtual environment
2. All dependencies are installed
3. PYTHONPATH includes the project root

### Type Checking False Positives

For FastHTML components, we use type stubs. If you get false positives:
1. Check the type stubs in `typings/fasthtml/`
2. Use `# type: ignore` sparingly for known issues
3. Update type stubs as needed

### Test Failures

If tests fail:
1. Check recent changes
2. Run specific failing test with `-v`
3. Check test fixtures in `conftest.py`
4. Ensure test database is clean
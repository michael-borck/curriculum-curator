# Contributing to Curriculum Curator

Thank you for your interest in contributing to Curriculum Curator! This document provides guidelines and instructions for contributing to the project.

## Development Environment Setup

1. Fork the repository
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/curriculum-curator.git
   cd curriculum-curator
   ```

3. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

We use several tools to ensure code quality:

- **Ruff**: For linting and formatting
- **isort**: For sorting imports
- **mypy**: For type checking

These tools are automatically run as pre-commit hooks. You can also run them manually:

```bash
ruff check .
ruff format .
isort .
mypy curriculum_curator
```

## Testing

We use pytest for testing. To run the tests:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=curriculum_curator
```

## Pull Request Process

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them with descriptive commit messages
3. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request against the main repository's `main` branch
5. Ensure that all checks pass (pre-commit, tests, etc.)

## Documentation

We use MkDocs for documentation. To build and serve the documentation locally:

```bash
mkdocs serve
```

## Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
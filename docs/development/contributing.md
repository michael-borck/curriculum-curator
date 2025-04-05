# Contributing to Curriculum Curator

Thank you for your interest in contributing to Curriculum Curator! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/curriculum-curator.git
   cd curriculum-curator
   ```

3. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

### Branching

- `main` branch is the stable version
- Create feature branches from `main` for your work
- Use a descriptive name for your branch, e.g., `feature/workflow-builder` or `fix/validation-issue`

### Testing

Run tests with pytest:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=curriculum_curator
```

### Code Style

We use several tools to ensure code quality:

- **Ruff**: For linting and formatting
- **Mypy**: For type checking
- **Pre-commit**: To run checks before committing

Run pre-commit on all files:

```bash
pre-commit run --all-files
```

### Documentation

- Update documentation for any new features or changes
- Run the documentation site locally:
  ```bash
  mkdocs serve
  ```

## Pull Request Process

1. Create a pull request from your feature branch to the `main` branch
2. Ensure all tests pass and the code meets style guidelines
3. Update documentation as needed
4. Add a clear description of the changes in the pull request
5. Request a review from at least one maintainer

## Release Process

1. Update the version number in `pyproject.toml`
2. Update the CHANGELOG.md file
3. Create a git tag for the version
4. Build the package
5. Upload to PyPI

See the [PyPI publishing guide](../guides/pypi-publishing.md) for detailed instructions.

## Project Structure

Understanding where to make changes is important. Here's a quick guide to the project structure:

- `curriculum_curator/`: Main package
  - `cli.py`: Command-line interface
  - `core.py`: Core functionality
  - `config/`: Configuration handling
  - `workflow/`: Workflow engine
  - `prompt/`: Prompt registry
  - `llm/`: LLM integration
  - `validation/`: Content validation
    - `validators/`: Individual validators
  - `remediation/`: Content remediation
    - `remediators/`: Individual remediators
  - `persistence/`: Session persistence
  - `utils/`: Utility functions
- `tests/`: Test suite
- `docs/`: Documentation
- `prompts/`: Example prompts
- `examples/`: Example configurations and workflows

## Adding New Components

### Adding a New Validator

1. Create a new file in `curriculum_curator/validation/validators/[category]/your_validator.py`
2. Implement a class that extends `BaseValidator`
3. Add your validator to the registry in `curriculum_curator/validation/validators/__init__.py`
4. Add tests in `tests/validation/validators/test_your_validator.py`

### Adding a New Remediator

1. Create a new file in `curriculum_curator/remediation/remediators/[category]/your_remediator.py`
2. Implement a class that extends `BaseRemediator`
3. Add your remediator to the registry in `curriculum_curator/remediation/remediators/__init__.py`
4. Add tests in `tests/remediation/remediators/test_your_remediator.py`

## Getting Help

If you have questions or need help with contributing, please:

1. Check the existing documentation
2. Open an issue on GitHub if you find a bug or have a feature request
3. Ask for clarification in an existing issue if needed

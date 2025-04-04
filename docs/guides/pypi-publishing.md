# Publishing to PyPI

This guide explains how to build and publish the Curriculum Curator package to PyPI.

## Prerequisites

1. Create accounts on [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/)
2. Generate API tokens for both PyPI and TestPyPI
3. Have the following packages installed:
   ```bash
   pip install build twine
   ```

## Setup PyPI Credentials

1. Copy the template file to your home directory:
   ```bash
   cp .pypirc.template ~/.pypirc
   ```

2. Edit the file with your tokens:
   ```bash
   nano ~/.pypirc
   ```

3. Replace the token placeholders with your actual tokens

## Building the Package

From the project root directory, run:

```bash
python -m build
```

This will create:
- A source distribution (`.tar.gz` file) in the `dist/` directory
- A wheel (`.whl` file) in the `dist/` directory

## Uploading to TestPyPI

Before uploading to the main PyPI repository, you should test the package on TestPyPI:

```bash
twine upload --repository testpypi dist/*
```

## Installing from TestPyPI

To verify the package works when installed from TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ curriculum-curator
```

Note: The `--extra-index-url` option is needed because TestPyPI doesn't have all the dependencies.

## Uploading to PyPI

Once you've verified the package works properly from TestPyPI, you can upload it to the main PyPI repository:

```bash
twine upload dist/*
```

## Version Management

1. Update the version number in `pyproject.toml` before each release
2. Follow semantic versioning: MAJOR.MINOR.PATCH
3. Create a git tag for each release:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
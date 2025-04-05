# Installation

Curriculum Curator is a Python package that can be installed using pip. This guide will help you set up the package and its dependencies.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

## Installing from PyPI

The simplest way to install Curriculum Curator is directly from PyPI:

```bash
pip install curriculum-curator
```

This will install the package along with all its dependencies.

## Development Installation

If you want to contribute to the development of Curriculum Curator, or use the latest development version, you can install it directly from the repository:

```bash
git clone https://github.com/teaching-repositories/curriculum-curator.git
cd curriculum-curator
pip install -e ".[dev]"
```

The `-e` flag installs the package in "editable" mode, allowing you to make changes to the code without having to reinstall. The `[dev]` extra installs development dependencies like pytest, ruff, and mypy.

## Verifying the Installation

After installation, you can verify that the package is correctly installed by running:

```bash
curator --version
```

You should see the version number of the installed package.

## Configuration

After installation, you'll need to configure the package with your LLM API credentials. You can do this by:

1. Creating a `config.yaml` file in your project directory:

```yaml
# LLM Configuration
llm:
  default:
    type: openai
    model: gpt-4-turbo
    api_key: your-api-key-here
    
  default_smart:
    type: anthropic
    model: claude-3-opus-20240229
    api_key: your-api-key-here

# Base paths
prompt_path: prompts/
output_path: output/
```

2. Alternatively, you can set environment variables for the API keys:

```bash
export OPENAI_API_KEY=your-api-key-here
export ANTHROPIC_API_KEY=your-api-key-here
```

## Next Steps

Once you have Curriculum Curator installed and configured, you can:

- [Get started with a quick tutorial](quick-start.md)
- [Learn about the interactive interface](../guides/interactive-mode.md)
- [Explore the workflow builder](../guides/workflow-builder.md)
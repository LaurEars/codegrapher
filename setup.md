# Setup and Release Guide

## Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) for package management
- System graphviz:
  - macOS: `brew install graphviz`
  - Ubuntu/Debian: `apt install graphviz`

## Development Setup

```bash
uv sync --extra dev
uv run pytest
```

## Building

```bash
uv build
```

This produces a wheel and sdist in `dist/`.

## Publishing

1. Verify the build:
   ```bash
   twine check dist/*
   ```

2. Upload to TestPyPI first:
   ```bash
   twine upload --repository testpypi dist/*
   ```

3. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

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

Publishing is automated via GitHub Actions using PyPI Trusted Publishing (OIDC — no stored tokens).

To release a new version:

1. Bump `version` in `pyproject.toml` and `codegrapher/__init__.py`
2. Commit and merge to `main`
3. Go to GitHub → Releases → Draft a new release
4. Create a tag `v<version>` targeting `main` (e.g. `v0.3.0`)
5. Fill in release notes and click Publish

The `publish` workflow triggers automatically and deploys to PyPI.

.PHONY: install install-dev test build check

install:
	uv sync

install-dev:
	uv sync --extra dev

test:
	uv run pytest

build:
	uv build

check:
	twine check dist/*

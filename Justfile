# https://github.com/casey/just

# Don't show the recipe name when running
set quiet

# Default recipe, it's run when just is invoked without a recipe
default:
  just --list --unsorted

# Sync dev dependencies
dev-sync:
    uv sync --all-extras --cache-dir .uv_cache

# Sync production dependencies (excludes dev dependencies)
prod-sync:
	uv sync --all-extras --no-dev --cache-dir .uv_cache

# Install pre commit hooks
install-hooks:
	uv run pre-commit install

# Run ruff formatting
format:
	uv run ruff format

# Run ruff linting and mypy type checking
lint:
	uv run ruff check --fix
	uv run mypy --ignore-missing-imports --install-types --non-interactive --package drafter

# Run tests using pytest
test:
	uv run pytest --verbose --color=yes tests

# Run only Python client library tests
test-python:
	uv run pytest --verbose --color=yes tests/test_client_library.py tests/test_starlette_server.py

# Run JavaScript/TypeScript tests
test-js:
	cd js && npm test

# Run all tests (Python + JS)
test-all: test test-js

# Test all examples
test-examples:
	python3 tools/test_examples.py

# Run all checks: format, lint, and test
validate: format lint test

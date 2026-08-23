# https://github.com/casey/just

# Don't show the recipe name when running
set quiet

# Default recipe, it's run when just is invoked without a recipe
default:
    just --list --unsorted

# Sync dev dependencies
dev-sync:
    uv sync --all-extras

# Sync production dependencies (excludes dev dependencies)
prod-sync:
    uv sync --all-extras --no-dev

# Install JS dependencies
js-install:
    cd js && npm install

# Install pre commit hooks
install-hooks:
    uv run pre-commit install

# Run ruff formatting
format:
    uv run ruff format

# Run ruff linting (with fixes) and mypy type checking
lint:
    uv run ruff check --fix
    uv run mypy --ignore-missing-imports --install-types --non-interactive --package drafter

check-docs:
    uv run python tools/doc_drift.py



# Check format/lint/types without modifying files (mirrors CI)
check:
    uv run ruff format --check
    uv run ruff check
    uv run mypy --ignore-missing-imports --install-types --non-interactive --package drafter

# Run JS unit tests (fast, no Pyodide)
test-js:
    cd js && npm test

# Run JS integration tests (real Pyodide, serial, large heap)
test-js-integration:
    cd js && npm run test:integration

watch-js:
    cd js && npm run watch

# Run Python tests
test-py:
    uv run pytest --verbose --color=yes tests

# Run all tests
test: test-js test-js-integration test-py

# Build JS assets into js/dist (needed by the compiler, docs, and packaging)
build-js:
    cd js && npm run build

# Build the Python sdist and wheel (bundles js/dist into drafter/assets)
build: build-js
    uv build

publish: build
    uv publish

# Build the documentation site into site/ (demos are compiled from js/dist)
docs: build-js
    uv run drafter-docs build

# Serve the documentation locally
docs-serve:
    uv run drafter-docs serve


# Run all checks: format, lint, and test
validate: format lint check-docs test

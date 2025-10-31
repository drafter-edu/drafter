# Drafter Testing Infrastructure

This directory contains the new testing infrastructure for the Drafter project, organized into two main categories:

## Test Categories

### 1. Bottle Server Tests (`test_bottle_server.py`)

Tests for the Bottle-based server to confirm that it works correctly with routes and state management.

**What is tested:**
- Server initialization
- Route registration (add_route and @route decorator)
- Server setup with initial state
- State management
- Multiple routes on the same server
- Server configuration

**How to run:**
```bash
pytest tests/test_bottle_server.py -v
```

### 2. Python Client Library Tests (`test_components.py`)

Unit tests for the Python client library components and the Page class.

**What is tested:**
- Page class (state and content handling, validation)
- Text components (Text, Header)
- Input components (TextBox, TextArea, CheckBox, SelectBox)
- Button and Link components
- Layout components (LineBreak, HorizontalRule, Div, Span)
- Table component
- Image component
- Route decorator functionality
- Component HTML rendering

**How to run:**
```bash
pytest tests/test_components.py -v
```

## Running All Tests

### Python Tests
```bash
pytest tests/test_bottle_server.py tests/test_components.py -v
```

or using the Justfile:
```bash
just test
```

## Test Philosophy

1. **Bottle Server Tests** - Simple tests that verify the server infrastructure works correctly with route management
2. **Python Client Library Tests** - Unit tests focusing on individual components and their interactions

## Notes

- The tests work with the current main branch structure where code is in `drafter/` (not `src/drafter/`)
- Tests use the Bottle-based server (not Starlette)
- The old test files in this directory (e.g., `test_simple_server.py`, `test_complex_form.py`) are legacy tests and may be deprecated
- Tests are written to be independent and can run in any order

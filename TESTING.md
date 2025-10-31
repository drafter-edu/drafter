# Testing Infrastructure

This document describes the new testing infrastructure for Drafter, which provides comprehensive tests for the Python library.

## Overview

The testing infrastructure is organized into two categories:

1. **Bottle Server Tests** - Tests for the server infrastructure
2. **Python Client Library Tests** - Unit tests for the Python API

## Test Categories

### 1. Bottle Server Tests

**Location:** `tests/test_bottle_server.py`

**Purpose:** Verify that the Bottle server works correctly with route management and state handling.

**Key Test Areas:**
- Server initialization and configuration
- Route registration (both add_route method and @route decorator)
- Server setup with initial state
- State management across routes
- Multiple routes on the same server

**Running:**
```bash
pytest tests/test_bottle_server.py -v
```

### 2. Python Client Library Tests

**Location:** `tests/test_components.py`

**Purpose:** Unit test the Python library that developers use to build Drafter applications.

**Key Test Areas:**
- `Page` class: state and content management, validation
- Text components: `Text`, `Header`
- Input components: `TextBox`, `TextArea`, `CheckBox`, `SelectBox`
- Interactive components: `Button`, `Link`
- Layout components: `LineBreak`, `HorizontalRule`, `Div`, `Span`
- `Table` component: data handling and rendering
- `Image` component: URL and dimensions
- `route` decorator: function decoration and route registration
- Component HTML rendering

**Running:**
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

## Test Dependencies

### Python
The following packages are required for testing:
- `pytest>=7.0.0`

Install with the full dev dependencies:
```bash
pip install -e ".[dev]"
```

## Legacy Tests

The following test files are part of the old testing infrastructure and may be deprecated:
- `tests/test_simple_server.py`
- `tests/test_complex_form.py`
- `tests/test_about_page.py`
- `tests/test_arguments.py`
- `tests/test_button_namespacing.py`
- `tests/test_unicode.py`

These tests use browser automation with Selenium/Chrome and are functional but use older patterns.

## Writing New Tests

### Python Tests

When writing new Python tests, follow these guidelines:

1. Use `pytest` fixtures for setup and teardown
2. Test one specific behavior per test function
3. Use descriptive test names following the pattern `test_<what>_<condition>`
4. Import only what you need from `drafter`
5. Create isolated test instances (don't rely on global state)

Example:
```python
def test_server_handles_state():
    """Test that server maintains state across route visits."""
    server = Server(_custom_name="TEST")
    server.setup({"count": 0})
    
    @route("increment", server=server)
    def increment(state):
        state["count"] += 1
        return Page(state, [f"Count: {state['count']}"])
    
    assert "increment" in server.routes
```

## Continuous Integration

The tests should be integrated into the CI pipeline. Recommended configuration:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/test_client_library.py tests/test_starlette_server.py -v

  test-js:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd js && npm ci
      - run: cd js && npm test
```

## Test Coverage

To generate coverage reports:

**Python:**
```bash
pytest --cov=src/drafter --cov-report=html tests/test_client_library.py tests/test_starlette_server.py
```

**JavaScript:**
```bash
cd js && npm run test:coverage
```

Coverage reports will be generated in `htmlcov/` (Python) and `js/coverage/` (JavaScript).

## Troubleshooting

### Python Tests Fail with Import Errors
Make sure you've installed the package in development mode:
```bash
pip install -e ".[dev]"
```

### Jest Tests Fail with Module Errors
Make sure you've installed npm dependencies:
```bash
cd js && npm install
```

### Starlette Tests Fail
Make sure the required dependencies are installed:
```bash
pip install starlette httpx pytest-asyncio
```

### Tests Pass Locally but Fail in CI
Check that all dependencies are listed in the correct requirements files and that the CI configuration installs them.

## Future Improvements

- Add integration tests that test the full stack (Python + JS)
- Add visual regression testing for UI components
- Add performance benchmarks
- Add mutation testing to verify test quality
- Expand coverage to include more edge cases

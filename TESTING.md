# Testing Infrastructure

This document describes the new testing infrastructure for Drafter, which replaces the old Bottle-based test system.

## Overview

The testing infrastructure is organized into three categories:

1. **Starlette Server Tests** - Tests for the local development server
2. **Python Client Library Tests** - Unit tests for the Python API
3. **TypeScript/Jest Tests** - End-to-end tests for the JavaScript client

## Test Categories

### 1. Starlette Server Tests

**Location:** `tests/test_starlette_server.py`

**Purpose:** Verify that the Starlette development server launches correctly and injects all necessary assets for local development.

**Key Test Areas:**
- Server startup and response handling
- HTML page structure and title injection
- User code embedding (inline and external)
- Skulpt library injection
- Drafter client library injection
- WebSocket configuration for hot reload
- Static assets routing
- WebSocket connection establishment

**Running:**
```bash
pytest tests/test_starlette_server.py -v
```

### 2. Python Client Library Tests

**Location:** `tests/test_client_library.py`

**Purpose:** Unit test the Python library that developers use to build Drafter applications.

**Key Test Areas:**
- `Router` class: route registration and retrieval
- `Server` class: initialization, state management, route visiting
- `route` decorator: function decoration and route registration
- `Page` class: state and content management, validation
- Component classes: `TextBox`, `Button`, `Text`, `Table`
- Component validation: parameter name checking
- `Response` class: page encapsulation

**Running:**
```bash
pytest tests/test_client_library.py -v
```

### 3. TypeScript/Jest Tests

**Location:** `js/tests/client.test.ts`

**Purpose:** End-to-end testing of the TypeScript client library that runs in the browser.

**Key Test Areas:**
- Client initialization with different target configurations
- Skulpt setup and configuration
- Code loading (inline and from URL)
- User interaction simulation (input, clicks, form submission)
- Page navigation (internal and external links)
- Component rendering (text, buttons, inputs, tables)
- DOM updates and state changes
- Form validation

**Running:**
```bash
cd js
npm test
```

**Watch mode:**
```bash
cd js
npm run test:watch
```

**Coverage report:**
```bash
cd js
npm run test:coverage
```

## Running All Tests

### Python Tests Only
```bash
pytest tests/test_client_library.py tests/test_starlette_server.py -v
```

or using the Justfile:
```bash
just test
```

### JavaScript Tests Only
```bash
cd js && npm test
```

### All Tests
```bash
# Terminal 1: Run Python tests
pytest tests/test_client_library.py tests/test_starlette_server.py -v

# Terminal 2: Run JavaScript tests
cd js && npm test
```

## Test Dependencies

### Python
The following packages are required for testing:
- `pytest>=7.0.0`
- `pytest-asyncio>=0.21.0`
- `starlette>=0.27.0`
- `httpx>=0.24.0`

Install with:
```bash
pip install -r tests/requirements-test.txt
```

Or install the full dev dependencies:
```bash
pip install -e ".[dev]"
```

### JavaScript
The following packages are required for testing:
- `jest`
- `ts-jest`
- `jest-environment-jsdom`
- `@types/jest`

Install with:
```bash
cd js
npm install
```

## Legacy Tests

The following test files are part of the old Bottle-based testing infrastructure and may be deprecated:
- `tests/test_simple_server.py`
- `tests/test_complex_form.py`
- `tests/test_about_page.py`
- `tests/test_arguments.py`
- `tests/test_button_namespacing.py`
- `tests/test_unicode.py`

These tests use `bottle`, `splinter`, and browser automation with Selenium/Chrome. They are functional but use outdated infrastructure.

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
    server = Server(custom_name="TEST")
    server.state = {"count": 0}
    
    @route("increment", server=server)
    def increment(state):
        state["count"] += 1
        return Page(state, [f"Count: {state['count']}"])
    
    response = server.visit("increment")
    assert server.state["count"] == 1
```

### TypeScript Tests

When writing new TypeScript tests, follow these guidelines:

1. Use `describe` blocks to group related tests
2. Use `beforeEach` to reset state between tests
3. Mock external dependencies (Skulpt, fetch, etc.)
4. Test both success and error cases
5. Simulate real user interactions

Example:
```typescript
describe('Component Rendering', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="app"></div>';
  });

  test('should render button component', () => {
    const app = document.getElementById('app')!;
    app.innerHTML = '<button>Click Me</button>';
    
    const button = app.querySelector('button');
    expect(button?.textContent).toBe('Click Me');
  });
});
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

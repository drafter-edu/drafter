# Drafter Testing Infrastructure

This directory contains the new testing infrastructure for the Drafter project, organized into three main categories:

## Test Categories

### 1. Starlette Server Tests (`test_starlette_server.py`)

Tests for the Starlette local development server to confirm that it successfully launches and injects the necessary components.

**What is tested:**
- Server launches and responds to requests
- HTML page contains the configured title
- User Python code is embedded or referenced correctly
- Skulpt library is injected
- Drafter client library is injected
- WebSocket URL for hot reload is configured
- Assets route is properly mounted
- WebSocket connection functionality

**How to run:**
```bash
pytest tests/test_starlette_server.py -v
```

### 2. Python Client Library Tests (`test_client_library.py`)

Unit tests for the Python client library that lets us build routes using components.

**What is tested:**
- Router class (route registration and retrieval)
- Server class (initialization, state management, visiting routes)
- Route decorator functionality
- Page class (state and content handling, validation)
- Components (TextBox, Button, Text, Table creation and validation)
- Response class

**How to run:**
```bash
pytest tests/test_client_library.py -v
```

### 3. TypeScript/Jest Tests (`js/tests/client.test.ts`)

End-to-end tests for the TypeScript client library that simulate actual user interactions.

**What is tested:**
- Client library initialization
- Target element selection
- Code loading (inline and from URL)
- Skulpt setup and configuration
- User interactions (text input, button clicks, form submissions)
- Page navigation (internal and external links)
- Component rendering (text, buttons, textboxes, tables)
- DOM updates on user actions

**How to run:**
```bash
cd js
npm test
```

For watch mode:
```bash
npm run test:watch
```

For coverage report:
```bash
npm run test:coverage
```

## Running All Tests

### Python Tests
```bash
pytest tests/ -v
```

or using the Justfile:
```bash
just test
```

### JavaScript Tests
```bash
cd js && npm test
```

## Test Philosophy

1. **Starlette Server Tests**: Simple tests that verify the server infrastructure works correctly
2. **Python Client Library Tests**: Unit tests focusing on individual components and their interactions
3. **TypeScript Tests**: Holistic end-to-end tests simulating real user workflows

## Dependencies

### Python
- pytest
- starlette
- httpx (for TestClient)

### JavaScript
- jest
- ts-jest
- jest-environment-jsdom
- @types/jest

## Notes

- The old test files in this directory (e.g., `test_simple_server.py`, `test_complex_form.py`) are legacy tests using the old Bottle-based infrastructure and may be deprecated.
- The new tests are designed to work with the modern Starlette-based server and the refactored client library.
- Tests are written to be independent and can run in any order.

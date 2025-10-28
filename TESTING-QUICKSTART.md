# Quick Start Guide for New Testing Infrastructure

This is a quick reference guide for developers who want to use or contribute to the new testing infrastructure.

## Quick Commands

### Python Tests
```bash
# Run all Python tests
pytest tests/test_client_library.py tests/test_starlette_server.py -v

# Run only client library tests
pytest tests/test_client_library.py -v

# Run only server tests
pytest tests/test_starlette_server.py -v

# Run with coverage
pytest --cov=src/drafter tests/test_client_library.py tests/test_starlette_server.py

# Run a specific test
pytest tests/test_client_library.py::TestRouter::test_add_route -v
```

### TypeScript Tests
```bash
# Run all TypeScript tests
cd js && npm test

# Run in watch mode (re-runs on file changes)
cd js && npm run test:watch

# Run with coverage
cd js && npm run test:coverage

# Run a specific test file
cd js && npm test -- client.test.ts

# Run tests matching a pattern
cd js && npm test -- --testNamePattern="Component Rendering"
```

### All Tests
```bash
# Python
pytest tests/test_client_library.py tests/test_starlette_server.py -v

# TypeScript (in a separate terminal)
cd js && npm test
```

## Installation

### Python Dependencies
```bash
# Option 1: Install all dev dependencies
pip install -e ".[dev]"

# Option 2: Install only test dependencies
pip install -r tests/requirements-test.txt
```

### TypeScript Dependencies
```bash
cd js
npm install
```

## Test Structure

```
tests/
├── README.md                      # Detailed test documentation
├── requirements-test.txt          # Python test dependencies
├── test_client_library.py         # Python client library unit tests
├── test_starlette_server.py       # Starlette server tests
├── conftest.py                    # Pytest configuration
└── helpers.py                     # Test helper functions

js/
├── jest.config.json               # Jest configuration
├── tests/
│   ├── setup.ts                   # Jest setup file
│   └── client.test.ts             # TypeScript client E2E tests
├── src/                           # Source files being tested
└── package.json                   # npm scripts and dependencies
```

## What Each Test File Tests

### `test_client_library.py`
- Router class (route management)
- Server class (server operations)
- Route decorator
- Page class (content and state)
- Components (TextBox, Button, Text, Table)
- Response class

### `test_starlette_server.py`
- Server startup
- HTML page generation
- Asset injection (Skulpt, Drafter client)
- WebSocket configuration
- Hot reload functionality
- Static file serving

### `client.test.ts`
- Client initialization
- Skulpt setup
- Component rendering
- User interactions
- Form handling
- Page navigation

## Common Tasks

### Adding a New Python Test
1. Open the appropriate test file (`test_client_library.py` or `test_starlette_server.py`)
2. Add a new test method to the relevant test class
3. Use descriptive names: `test_<what>_<condition>`
4. Run the test to verify it works

Example:
```python
def test_button_with_custom_style(self):
    """Test creating a Button with custom styling."""
    button = Button("Styled", lambda s: Page(s, []), style="color: red;")
    assert "style" in str(button)
```

### Adding a New TypeScript Test
1. Open `js/tests/client.test.ts`
2. Add a new test case within the appropriate `describe` block
3. Use descriptive names: `should <expected behavior>`
4. Run the test to verify it works

Example:
```typescript
test('should handle disabled buttons', () => {
  const button = document.createElement('button');
  button.disabled = true;
  expect(button.disabled).toBe(true);
});
```

### Running Tests Before Committing
```bash
# Run Python tests
pytest tests/test_client_library.py tests/test_starlette_server.py -v

# Run TypeScript tests
cd js && npm test

# If both pass, you're good to commit!
```

## Debugging Failing Tests

### Python Tests
```bash
# Run with verbose output
pytest tests/test_client_library.py -vv

# Run with print statements shown
pytest tests/test_client_library.py -s

# Drop into debugger on failure
pytest tests/test_client_library.py --pdb

# Run only failed tests from last run
pytest --lf
```

### TypeScript Tests
```bash
# Run with verbose output
cd js && npm test -- --verbose

# Run a single test file
cd js && npm test -- client.test.ts

# Run in watch mode and only re-run changed tests
cd js && npm run test:watch
```

## Continuous Integration

The tests are designed to run in CI. See `.github/workflows/test-example.yml` for an example GitHub Actions configuration.

Key points:
- Tests run on multiple Python versions (3.8-3.12)
- TypeScript tests run on Node.js 18
- Coverage reports are generated
- Tests must pass before merging

## Getting Help

- **Test Documentation:** See `tests/README.md` for detailed information
- **Full Testing Guide:** See `TESTING.md` in the root directory
- **Issues:** Report test-related issues on GitHub with the `testing` label

## Quick Troubleshooting

**Problem:** `ModuleNotFoundError: No module named 'pytest'`
**Solution:** `pip install -e ".[dev]"` or `pip install pytest`

**Problem:** `Cannot find module 'jest'`
**Solution:** `cd js && npm install`

**Problem:** Tests pass locally but fail in CI
**Solution:** Check that all dependencies are listed in requirements files

**Problem:** TypeScript compilation errors
**Solution:** This is expected for now; the tests mock Skulpt globals

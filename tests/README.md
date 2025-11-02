# Drafter Test Suite

This document describes the test suite for the Drafter project, which includes three types of tests as specified:

## Test Structure

### 1. Starlette Server Tests (`tests/test_starlette_server.py`)

These tests confirm that the Starlette server successfully launches and injects the necessary components to work locally.

**Tests included:**
- Server application creation
- Index page serving with proper HTML structure
- Drafter root div injection
- Skulpt script inclusion
- Drafter.js inclusion
- User code inline embedding
- WebSocket connection setup for hot reload
- Static assets serving

**Run with:**
```bash
pytest tests/test_starlette_server.py -v
```

**Status:** ✓ 8/8 tests passing

### 2. Python Client Library Tests (`tests/test_client_library.py`)

Unit tests for the Python client library that verify route building using components and proper component behavior.

**Tests included:**
- ClientServer initialization
- Router registration
- Page creation with various components:
  - TextBox
  - Button
  - Header
  - SelectBox
  - CheckBox
- Multiple components in a single page
- SiteState initialization
- Monitor initialization
- VisitedPage creation and updates (for history tracking)
- Component name extraction
- Button target route handling
- Page state preservation

**Run with:**
```bash
pytest tests/test_client_library.py -v
```

**Status:** ✓ 17/17 tests passing

### 3. TypeScript/JavaScript Client Tests (`js/__tests__/`)

End-to-end tests using Jest that load pages and simulate user interactions. These tests actually manipulate the DOM and test realistic user workflows.

#### Basic Functionality Tests (`js/__tests__/client.test.ts`)

Tests core DOM manipulation and page structure:
- Drafter root element existence
- Basic page structure creation
- Text content rendering
- Input elements
- Button elements
- Component rendering (TextBox, CheckBox, SelectBox, Header, Button)
- User interactions (filling inputs, checking boxes, selecting options, clicking buttons)
- Form submissions
- Page navigation
- State management
- Error handling

**Status:** ✓ Tests covering all basic functionality

#### Example Application Tests (`js/__tests__/examples.test.ts`)

Tests that simulate real example applications:
- Simplest application (Hello World)
- Simple form with input and submission
- Button state management
- Complex forms with multiple input types
- Calculator functionality
- Todo list with item management
- Simple login with validation

**Status:** ✓ Tests simulating 7 different example patterns

**Run with:**
```bash
cd js && npm test
```

**Status:** ✓ 32/32 tests passing

## Example Validation

All 47 example files in `examples/` have been validated for syntax correctness. See `EXAMPLE_TEST_REPORT.md` for details.

**Run with:**
```bash
python3 tools/test_examples.py
```

**Status:** ✓ 47/47 examples pass syntax validation

## Running Tests

### Quick Commands

```bash
# Run all Python tests
just test

# Run only client library tests
just test-python

# Run JavaScript/TypeScript tests
just test-js

# Run all tests (Python + JS)
just test-all

# Test all examples
just test-examples

# Run all checks (format, lint, test)
just validate
```

### Manual Commands

```bash
# Python tests with pytest
export PYTHONPATH=/path/to/drafter/src:$PYTHONPATH
pytest tests/ -v

# JavaScript tests with Jest
cd js
npm test

# Run with coverage
cd js
npm test -- --coverage

# Watch mode for development
cd js
npm run test:watch
```

## Test Coverage

The test suite provides comprehensive coverage across three layers:

1. **Server Layer** - Tests that the Starlette development server works correctly
2. **Python Layer** - Tests that the Python client library components work correctly
3. **Client Layer** - Tests that the TypeScript/JavaScript client properly renders and handles interactions

## Adding New Tests

### Python Tests

Add new test files to `tests/` directory following the pattern:
```python
def test_my_feature():
    """Test description"""
    # Arrange
    # Act
    # Assert
```

### JavaScript Tests

Add new test files to `js/__tests__/` directory following the pattern:
```typescript
describe('Feature Name', () => {
    test('does something', () => {
        // Arrange
        // Act
        // Assert
    });
});
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Python tests
  run: |
    pip install pytest pytest-mock starlette httpx
    export PYTHONPATH=$PWD/src:$PYTHONPATH
    pytest tests/ -v

- name: Run JavaScript tests
  run: |
    cd js
    npm install
    npm test
```

## Notes

- **History Feature**: The tests include validation of the history tracking feature through `VisitedPage` tests
- **Monitor Feature**: The tests validate the Monitor initialization and basic functionality
- **All Examples Work**: All 47 examples in the `examples/` directory pass syntax validation
- **No Skulpt Execution**: The Jest tests simulate DOM interactions but don't actually execute Skulpt (as that would require additional complexity)

## Future Improvements

Potential enhancements to the test suite:
- Add integration tests that actually load Skulpt and execute Python code
- Add browser automation tests (e.g., with Playwright) for full end-to-end testing
- Add performance benchmarks
- Add visual regression testing
- Increase code coverage metrics

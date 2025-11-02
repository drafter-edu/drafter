# Drafter Test Suite

This directory contains three types of tests for the Drafter framework:

## 1. Starlette Server Tests (`test_starlette_server.py`)

These tests verify that the Starlette development server:
- Launches successfully
- Serves the main index page
- Injects necessary JavaScript and assets
- Provides WebSocket support for hot reloading
- Serves static assets correctly

**Run with:**
```bash
pytest tests/test_starlette_server.py -v
```

## 2. Python Client Library Tests

### Component Tests (`test_components.py`)
Unit tests for individual Drafter components:
- Page creation with various content types
- TextBox, Button, Header, TextArea components
- SelectBox, CheckBox components
- List components (NumberedList, BulletedList)
- Table, Link, Image components
- Layout components (Div, Span, LineBreak, HorizontalRule)
- Complex nested page structures

**Run with:**
```bash
pytest tests/test_components.py -v
```

### Route Tests (`test_routes.py`)
Unit tests for route building and navigation:
- Route decorator functionality
- State management across routes
- Form parameter handling
- Button navigation
- Route registration and naming
- State updates and persistence

**Run with:**
```bash
pytest tests/test_routes.py -v
```

## 3. TypeScript/Jest End-to-End Tests (in `js/__tests__/`)

These tests provide comprehensive end-to-end testing using Jest and Playwright:

### Basic Tests (`basic.test.ts`)
Simple unit tests for TypeScript client functionality

### Examples E2E Tests (`examples-e2e.test.ts`)
End-to-end tests for specific examples:
- Simple examples (simplest, simple_state)
- Button examples (button_state)
- Form examples (simple_form, complex_form)
- Calculator examples
- List examples (todo_list)
- Navigation examples
- State examples
- UI component examples
- Styling examples
- Error handling examples

### Comprehensive Examples Test (`all-examples.test.ts`)
Tests ALL examples in the `examples/` directory and generates:
- JSON report of all test results
- Markdown report with working and failing examples
- Detailed error messages for failures

**Run with:**
```bash
cd js
npm test
```

**Run specific test:**
```bash
cd js
npm test -- examples-e2e.test.ts
```

**Generate full report:**
```bash
cd js
npm test -- all-examples.test.ts
```

The report will be generated in `js/test-results/`:
- `examples-test-report.json` - Detailed JSON results
- `examples-test-report.md` - Readable markdown summary

## Test Infrastructure

### Python Tests
- Framework: pytest
- Server testing: Starlette TestClient
- Dependencies: pytest, pytest-cov, starlette

### JavaScript/TypeScript Tests
- Framework: Jest with ts-jest
- E2E Testing: Playwright
- Environment: jsdom for DOM testing
- Configuration: `js/jest.config.js`

## Running All Tests

**Python tests:**
```bash
pytest tests/ -v
```

**JavaScript tests:**
```bash
cd js && npm test
```

**Full test suite:**
```bash
just test  # Uses Justfile
# or
pytest tests/ -v && cd js && npm test
```

## Test Results

Test results and reports are saved to:
- `js/test-results/` - Jest test reports (gitignored)
- `tests/fixtures/` - Temporary test fixtures (gitignored)
- Coverage reports in `htmlcov/` (gitignored)

## Writing New Tests

### Python Component Tests
Add to `tests/test_components.py`:
```python
def test_new_component():
    component = NewComponent("param")
    assert component is not None
```

### Python Route Tests
Add to `tests/test_routes.py`:
```python
def test_new_route_feature():
    test_server = ClientServer()
    
    @route(server=test_server)
    def my_route(state: str) -> Page:
        return Page(state, ["Content"])
    
    assert "my_route" in [r.name for r in test_server.routes]
```

### Jest E2E Tests
Add to `js/__tests__/`:
```typescript
test('new example test', async () => {
    const { page, error } = await loadExample('example_name');
    await page.waitForTimeout(1000);
    // Add assertions
    await page.close();
});
```

## Known Issues

As documented by the comprehensive test suite, some examples may fail during testing. Check `js/test-results/examples-test-report.md` for the current status of all examples.

# Quick Start Guide for New Testing Infrastructure

This is a quick reference guide for developers who want to use or contribute to the new testing infrastructure.

## Quick Commands

### Python Tests
```bash
# Run all Python tests
pytest tests/test_bottle_server.py tests/test_components.py -v

# Run only server tests
pytest tests/test_bottle_server.py -v

# Run only component tests
pytest tests/test_components.py -v

# Run with coverage
pytest --cov=drafter tests/test_bottle_server.py tests/test_components.py

# Run a specific test
pytest tests/test_components.py::TestPage::test_page_with_state_and_content -v
```

## Installation

### Python Dependencies
```bash
# Option 1: Install all dev dependencies
pip install -e ".[dev]"

# Option 2: Just install pytest
pip install pytest
```

## Test Structure

```
tests/
├── README.md                      # Detailed test documentation
├── test_bottle_server.py          # Bottle server tests
├── test_components.py             # Python client library tests
├── conftest.py                    # Pytest configuration
└── helpers.py                     # Test helper functions (legacy)
```

## What Each Test File Tests

### `test_bottle_server.py`
- Server class initialization and configuration
- Route registration (add_route and @route decorator)
- Server setup with initial state
- State management
- Multiple routes

### `test_components.py`
- Page class (content and state)
- Text components (Text, Header)
- Input components (TextBox, TextArea, CheckBox, SelectBox)
- Interactive components (Button, Link)
- Layout components (LineBreak, HorizontalRule, Div, Span)
- Table component
- Image component
- Component HTML rendering

## Common Tasks

### Adding a New Python Test
1. Open the appropriate test file (`test_bottle_server.py` or `test_components.py`)
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

### Running Tests Before Committing
```bash
# Run all tests
pytest tests/test_bottle_server.py tests/test_components.py -v

# If they pass, you're good to commit!
```

## Debugging Failing Tests

### Python Tests
```bash
# Run with verbose output
pytest tests/test_components.py -vv

# Run with print statements shown
pytest tests/test_components.py -s

# Drop into debugger on failure
pytest tests/test_components.py --pdb

# Run only failed tests from last run
pytest --lf
```

## Getting Help

- **Test Documentation:** See `tests/README.md` for detailed information
- **Full Testing Guide:** See `TESTING.md` in the root directory
- **Issues:** Report test-related issues on GitHub with the `testing` label

## Quick Troubleshooting

**Problem:** `ModuleNotFoundError: No module named 'pytest'`
**Solution:** `pip install -e ".[dev]"` or `pip install pytest`

**Problem:** `ModuleNotFoundError: No module named 'drafter'`
**Solution:** `pip install -e .` to install drafter in editable mode

**Problem:** Tests pass locally but fail in CI
**Solution:** Check that all dependencies are listed in requirements files

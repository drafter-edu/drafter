# JS Bridge Architecture

This document explains the architecture of the JS bridge module that enables Python code to interact with JavaScript/DOM APIs across both Skulpt and Pyodide runtimes.

## Overview

The bridge consists of two main components:

1. **`js.ts`** (TypeScript/Skulpt Module): Provides a Skulpt-compatible implementation of the `js` package that Pyodide offers natively
2. **`client.py`** (Python Module): A pure Python implementation of the bridge client that uses the `js` package for DOM manipulation

## Architecture

### Skulpt Implementation (`js/src/bridge/js.ts`)

This TypeScript module gets compiled into a Skulpt built-in module that provides:

- **`js.document`**: Proxy object for DOM document access
  - Methods: `createElement()`, `getElementById()`, `getElementsByTagName()`, `querySelectorAll()`, `createRange()`
  - Properties: `title`
  - Event handling: `addEventListener()`, `removeEventListener()`

- **`js.window`**: Proxy object for window access
  - Methods: `scrollTo()`
  - Event handling: `addEventListener()`, `removeEventListener()`
  
- **`js.scrollX` / `js.scrollY`**: Dynamic properties returning current scroll position

- **`js.FormData`**: Wrapper class for FormData objects
  - Methods: `append()`, `delete()`, `get()`, `has()`

- **DOM Element Proxies**: Automatic wrapping of DOM elements with Python-friendly interfaces
  - All standard DOM methods and properties
  - Event handling support

- **Event Proxies**: Wrapper for DOM events
  - Access to event properties: `target`, `key`, `ctrlKey`, `metaKey`, etc.
  - Methods: `preventDefault()`, `stopPropagation()`

### Python Implementation (`src/drafter/bridge/client.py`)

Pure Python implementation that:

- Uses the `js` package for all DOM interactions
- Implements all bridge functions:
  - `replaceHTML()`: Updates DOM content while preserving scroll
  - `update_site()`: Handles page updates and navigation mounting
  - `setup_navigation()`: Sets up browser navigation handlers
  - `set_site_title()`: Updates document title
  - `register_hotkey()`: Registers keyboard shortcuts
  - `console_log()`: Logs to browser console
  - `setup_debug_menu()`: Initializes debug panel
  - `handle_event()`: Processes telemetry events

## Key Features

### Cross-Runtime Compatibility

The same Python code works in both:
- **Skulpt**: Uses the TypeScript-implemented `js` module
- **Pyodide**: Uses Pyodide's native `js` package

### Event Handling

Event listeners are properly managed with:
- Automatic Python callback wrapping
- Event proxy objects for accessing event properties
- Cleanup support via `removeEventListener()`

### Type Safety

While Python doesn't enforce types at runtime, the implementation:
- Uses type hints for better IDE support
- Follows the same patterns as Pyodide's `js` package
- Provides consistent behavior across runtimes

## Usage Example

```python
import js
from drafter.bridge.client import replaceHTML, set_site_title

# Set page title
set_site_title("My Application")

# Update DOM content
element = js.document.getElementById("content")
replaceHTML(element, "<p>New content</p>")

# Add event listener
def handle_click(event):
    event.preventDefault()
    print("Button clicked!")

button = js.document.getElementById("myButton")
button.addEventListener("click", handle_click)
```

## Build Process

1. TypeScript files in `js/src/bridge/` are compiled to JavaScript
2. Python files in `src/drafter/bridge/` are compiled to Skulpt modules
3. Both are bundled into `src/drafter/assets/js/skulpt-drafter.js`
4. The `js.ts` module is registered as `src/lib/drafter/bridge/js.js`
5. The `client.py` module is registered as `src/lib/drafter/bridge/client.js`

## Testing

The implementation can be tested by:
1. Running the existing Skulpt tests (when TypeScript errors are fixed)
2. Creating test pages that import and use the bridge
3. Verifying Pyodide compatibility with the same Python code

## Future Enhancements

Potential improvements:
- Complete FormData support with proper data extraction
- URL manipulation utilities
- Additional DOM API coverage as needed
- Better error handling and debugging support

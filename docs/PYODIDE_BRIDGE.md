# Pyodide Bridge for Drafter

This document describes the Pyodide bridge implementation for Drafter, which provides an alternative to the Skulpt runtime.

## Overview

Drafter now supports two Python runtimes for running Python code in the browser:

1. **Skulpt** (original): A Python-to-JavaScript transpiler
2. **Pyodide** (new): Full CPython compiled to WebAssembly

## Key Differences

### Skulpt
- Lightweight and fast startup
- Python 3 syntax but limited library support
- Custom module system with `$builtinmodule`
- Uses `import document` for DOM access
- Bridge compiled into Skulpt as built-in module
- Sets `sys.platform` to `"skulpt"`

### Pyodide
- Full CPython 3.11 with extensive library support
- Slower startup but more complete Python implementation
- Standard Python import system
- Uses `from js import document` for DOM access
- Bridge registered as JavaScript module
- Sets `sys.platform` to `"emscripten"`

## Runtime Detection

Both Skulpt and Pyodide are detected by the existing `is_skulpt()` function in `drafter.utils`, which checks if `sys.platform` is in `("skulpt", "emscripten")`. This means existing code that uses `is_skulpt()` will work correctly with both runtimes without modification.

## Architecture Changes

### Python Side

The Python bridge code now supports both runtimes:

```python
# drafter/bridge/helpers.py and __init__.py
try:
    # Pyodide
    from js import document
except ImportError:
    # Skulpt
    import document
```

This allows the same Python code to work in both environments.

### JavaScript Side

New files added:
- `js/src/bridge/client_pyodide.ts` - Pyodide-specific bridge implementation
- `js/src/pyodide-tools.ts` - Pyodide setup and runtime utilities
- Updated `js/src/index.ts` - Supports both runtimes

The bridge is registered with Pyodide using `pyodide.registerJsModule()`:

```javascript
const bridgeModule = createPyodideBridge();
pyodide.registerJsModule("drafter.bridge.client", bridgeModule);
```

## Usage

### In HTML

```html
<!-- Load Pyodide -->
<script src="https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js"></script>

<!-- Load Drafter -->
<script src="drafter.js"></script>

<script>
  // Run with Pyodide
  runStudentCode({
    code: pythonCode,
    runtime: 'pyodide',  // or 'skulpt' (default)
    presentErrors: true,
    pyodideIndexURL: 'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/'  // optional
  });
</script>
```

### Programmatic API

```javascript
import { setupPyodide, startServerPyodide } from 'drafter';

// Initialize Pyodide with optional custom CDN URL
await setupPyodide('https://cdn.jsdelivr.net/pyodide/v0.25.0/full/');

// Run Python code
await startServerPyodide(pythonCode);
```

## Testing

See `examples/pyodide_example.html` for a working example.

To test locally:
1. Build the project: `cd js && npm run build`
2. Serve the examples directory with a local web server
3. Open `pyodide_example.html` in a browser

## Migration Guide

### For Users

Most Drafter code should work without changes. The main difference is specifying the runtime:

```javascript
// Old (Skulpt only)
runStudentCode({ code: pythonCode });

// New (choose runtime)
runStudentCode({ code: pythonCode, runtime: 'skulpt' });  // Default
runStudentCode({ code: pythonCode, runtime: 'pyodide' });  // Use Pyodide
```

### For Developers

When extending the bridge:

1. **Add functions to both bridge implementations:**
   - `js/src/bridge/client.ts` (Skulpt)
   - `js/src/bridge/client_pyodide.ts` (Pyodide)

2. **Update Python stubs:**
   - `src/drafter/bridge/client.py`

3. **Handle document access:**
   - Use the try/except pattern in Python files that access the DOM

4. **Test both runtimes:**
   - Ensure functionality works in both Skulpt and Pyodide
   - Remember that `is_skulpt()` returns True for both runtimes

## Performance Considerations

- **Startup**: Pyodide takes ~2-5 seconds to load initially, Skulpt is nearly instant
- **Execution**: Pyodide is generally faster for compute-heavy tasks
- **Package support**: Pyodide supports many more Python packages
- **Bundle size**: Pyodide is ~10MB, Skulpt is ~500KB

## References

- [Pyodide Documentation](https://pyodide.org/)
- [Skulpt Documentation](https://skulpt.org/)
- [Pyodide JavaScript API](https://pyodide.org/en/stable/usage/api/js-api.html)

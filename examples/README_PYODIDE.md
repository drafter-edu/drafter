# Testing the Pyodide Bridge

This directory contains an example HTML file (`pyodide_example.html`) that demonstrates how to use Drafter with Pyodide instead of Skulpt.

## Prerequisites

1. Build the JavaScript files:
   ```bash
   cd ../js
   npm install
   npm run build
   ```

2. Start a local web server (required because browsers restrict loading local files):
   ```bash
   # Option 1: Python's built-in server
   python3 -m http.server 8000
   
   # Option 2: Node.js http-server
   npx http-server -p 8000
   
   # Option 3: PHP's built-in server
   php -S localhost:8000
   ```

3. Open the example in your browser:
   ```
   http://localhost:8000/examples/pyodide_example.html
   ```

## What to Expect

When you open the page:
1. You'll see "Loading Pyodide..." (takes 2-5 seconds)
2. The status will change to "Initializing Drafter with Pyodide..."
3. Finally, you'll see "Drafter loaded successfully with Pyodide!"
4. The example page will render with a header saying "Hello from Pyodide!"

## Troubleshooting

### "Pyodide loader not found"
Make sure you have internet connection - Pyodide is loaded from CDN.

### "Failed to fetch drafter.js"
Make sure you built the JavaScript files and are running a web server (see Prerequisites).

### Page loads but nothing appears
Check the browser console (F12) for error messages.

### Slow loading
Pyodide is ~10MB and takes several seconds to load the first time. Subsequent loads may be faster due to browser caching.

## Comparing with Skulpt

To compare with the Skulpt runtime:

1. Edit `pyodide_example.html`
2. Change `runtime: 'pyodide'` to `runtime: 'skulpt'`
3. Comment out the Pyodide script tag
4. Add Skulpt script tags (see other examples or the main Drafter documentation)

## Key Differences

- **Skulpt**: Loads instantly, limited Python features
- **Pyodide**: Takes ~2-5 seconds to load, full Python 3.11 with many packages

## Creating Your Own Pyodide Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Drafter Pyodide App</title>
</head>
<body>
    <div id="drafter-root--"></div>
    
    <!-- Load Pyodide from CDN -->
    <script src="https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js"></script>
    
    <!-- Load Drafter -->
    <script src="../js/dist/js/drafter.js"></script>
    
    <script>
        const pythonCode = `
from drafter import *

@route
def index():
    return Page(None, [
        Header("My Pyodide App", 1),
        "This is running on Pyodide!"
    ])

start_server()
`;

        window.runStudentCode({
            code: pythonCode,
            runtime: 'pyodide',
            presentErrors: true
        }).catch(err => console.error(err));
    </script>
</body>
</html>
```

## Additional Resources

- [Pyodide Documentation](https://pyodide.org/)
- [Drafter Pyodide Bridge Documentation](../docs/PYODIDE_BRIDGE.md)
- [Implementation Summary](../docs/IMPLEMENTATION_SUMMARY.md)

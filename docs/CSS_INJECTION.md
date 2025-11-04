# CSS and JavaScript Injection in Drafter V2

Drafter V2 provides two elegant ways to add custom CSS and JavaScript to your web applications:

1. **Pre-start Configuration**: Add CSS/JS before calling `start_server()` - applies to the entire site
2. **Dynamic Injection**: Add CSS/JS from within route functions - applies when specific pages are rendered

## Approach 1: Pre-start Configuration

Call the configuration functions before `start_server()` to add CSS and JS that will be included in the initial site HTML:

```python
from drafter import route, start_server, Page, add_website_css, add_website_header, set_website_title
from dataclasses import dataclass

# Add CSS before start_server - applies to entire site
add_website_css("""
body {
    font-family: Arial, sans-serif;
    background-color: #f0f0f0;
}
.highlight {
    background-color: yellow;
    padding: 5px;
}
""")

# Or add CSS with selector and content separately
add_website_css(".error", "color: red; font-weight: bold;")

# Add custom header content (e.g., meta tags, external stylesheets)
add_website_header('<link rel="stylesheet" href="https://example.com/custom.css">')

# Set website title
set_website_title("My Custom App")

@dataclass
class State:
    message: str = "Hello World"

@route
def index(state: State) -> Page:
    return Page(state, [
        "<div class='highlight'>This is highlighted text</div>",
        state.message
    ])

start_server(State())
```

### Available Pre-start Functions

- `add_website_css(selector, css=None)`: Add CSS to the site
  - If only `selector` is provided, it's treated as raw CSS content
  - If both parameters are provided, creates a CSS rule: `selector { css }`
- `add_website_header(header)`: Add raw HTML header content
- `set_website_title(title)`: Set the page title
- `set_website_framed(framed)`: Set whether the site is framed (default: True)
- `set_website_style(style)`: Set the CSS framework (e.g., "skeleton", "bootstrap", "none")
- `hide_debug_information()`: Hide debug information (useful for deployment)
- `show_debug_information()`: Show debug information (default in development)

## Approach 2: Dynamic Injection via Routes

Add CSS and JavaScript dynamically from within route functions by passing them as parameters to `Page`:

```python
from drafter import route, start_server, Page, Button
from dataclasses import dataclass

@dataclass
class State:
    theme: str = "light"
    count: int = 0

@route
def index(state: State) -> Page:
    # Determine CSS based on state
    if state.theme == "dark":
        css = [".content { background: #333; color: #fff; }"]
    else:
        css = [".content { background: #fff; color: #000; }"]
    
    return Page(
        state,
        [
            "<div class='content'>",
            f"Current theme: {state.theme}",
            f"Count: {state.count}",
            Button("Toggle Theme", toggle_theme),
            Button("Increment", increment),
            "</div>"
        ],
        css=css  # Dynamic CSS injected when this page renders
    )

@route
def toggle_theme(state: State) -> Page:
    state.theme = "dark" if state.theme == "light" else "light"
    return index(state)

@route
def increment(state: State) -> Page:
    state.count += 1
    
    # Add JavaScript to show an alert
    js = [f"alert('Count incremented to {state.count}!');"]
    
    page = index(state)
    page.js = js  # Add JavaScript that will execute after page loads
    return page

start_server(State())
```

### Page Parameters

The `Page` class accepts these optional parameters:

- `css`: A list of CSS strings to inject when the page is rendered
- `js`: A list of JavaScript strings to inject and execute when the page is rendered

```python
Page(
    state,
    content_list,
    css=["#special { color: red; }"],
    js=["console.log('Page loaded');"]
)
```

## How It Works

### Pre-start Configuration

1. Functions like `add_website_css()` modify the `MAIN_SERVER.configuration`
2. When `start_server()` is called, the configuration is processed
3. CSS/header content is added to the `Site` object
4. When the site renders, CSS is wrapped in `<style>` tags and included in the initial HTML

### Dynamic Injection

1. Route functions return a `Page` with `css` and `js` lists
2. The `ClientServer` creates a `Response` and adds these to channels:
   - CSS is added to the "before" channel as "style" messages
   - JS is added to the "after" channel as "script" messages
3. The `ClientBridge` processes channel messages:
   - "style" messages create `<style>` tags in the document head
   - "script" messages create `<script>` tags in the document head
4. Content is deduplicated using sigils (optional parameter to prevent duplicate injection)

## Best Practices

1. **Use pre-start configuration for site-wide styles**: Base styles, layout, and theme CSS
2. **Use dynamic injection for page-specific styles**: Conditional styling based on state or user interactions
3. **Combine both approaches**: Set a base theme with pre-start, then add dynamic variations per page
4. **Keep CSS organized**: Group related styles together, use clear class names
5. **Test in development mode**: Debug information helps verify CSS is applied correctly

## Examples

See the `examples/` directory for complete working examples:
- `examples/fun_style.py` - Dynamic CSS based on state
- `examples/deployed_full_width.py` - Pre-start CSS configuration
- `examples/styling_example.py` - Combining both approaches

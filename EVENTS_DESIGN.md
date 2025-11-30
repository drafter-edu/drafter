# Event System Design for Drafter

## Overview

This document outlines the design for an event system in Drafter that allows functions to return different response types (`Update`, `Fragment`) and be triggered by various HTML events beyond just page navigation.

## New Return Types

### 1. Update

**Purpose**: Update the server state without modifying the page HTML.

**Use Cases**:
- Background state updates
- Analytics/tracking events
- Form validation that doesn't require visual feedback
- State synchronization

**Signature**:
```python
Update(state: Any)
```

**Example**:
```python
@route
def track_click(state: AppState) -> Update:
    state.click_count += 1
    return Update(state)
```

**Server Behavior**:
- Updates internal state
- Returns JSON response: `{"type": "update", "success": True}`
- No HTML re-rendering

### 2. Fragment

**Purpose**: Update a specific element on the page without full page refresh.

**Use Cases**:
- Updating a counter display
- Refreshing a single section of data
- Toggling visibility of elements
- Dynamic form field updates

**Signature**:
```python
Fragment(state: Any, target: str, content: Union[List, str, PageContent])
```

**Parameters**:
- `state`: New state to store on server
- `target`: CSS selector for the element to update
- `content`: HTML content to render into the target element

**Example**:
```python
@route
def increment_counter(state: AppState) -> Fragment:
    state.counter += 1
    return Fragment(
        state=state,
        target="#counter-display",
        content=[f"Count: {state.counter}"]
    )
```

**Server Behavior**:
- Updates internal state
- Renders only the Fragment content
- Returns JSON response: `{"type": "fragment", "target": "#selector", "content": "<html>"}`
- Client-side JavaScript updates the target element

### 3. Page (Existing)

**Purpose**: Full page replacement with new content.

**Current Behavior**: Continues to work as before.

## Event System

### Client-Side Event Handlers

Components can accept event handler parameters that reference functions returning `Update`, `Fragment`, or `Page`:

#### Button Events

```python
Button(
    text="Click Me",
    on_click=handle_click,  # Function returning Update/Fragment/Page
    arguments=[...]
)
```

**Supported Button Events**:
- `on_click`: Triggered when button is clicked (default behavior for regular buttons)

#### TextBox Events

```python
TextBox(
    name="search",
    on_change=handle_search,     # Triggered when value changes
    on_blur=handle_blur,         # Triggered when focus is lost
    on_keyup=handle_keyup        # Triggered on key release
)
```

**Supported TextBox Events**:
- `on_change`: Value changes and loses focus
- `on_input`: Value changes (every keystroke)
- `on_blur`: Element loses focus
- `on_focus`: Element gains focus
- `on_keyup`: Key is released
- `on_keydown`: Key is pressed

#### SelectBox Events

```python
SelectBox(
    name="category",
    options=["A", "B", "C"],
    on_change=handle_category_change
)
```

**Supported SelectBox Events**:
- `on_change`: Selection changes

#### CheckBox Events

```python
CheckBox(
    name="agree",
    on_change=handle_checkbox_change
)
```

**Supported CheckBox Events**:
- `on_change`: Checkbox state changes

### Server-Side Implementation

Each event handler function should have a signature like:

```python
def handle_event(state: State, *params) -> Union[Page, Update, Fragment]:
    # Process event
    # Return appropriate response type
    pass
```

### Client-Side JavaScript

A lightweight JavaScript handler will:

1. Intercept events on elements with handlers
2. Serialize form data and event information
3. Make AJAX POST request to the handler function's route
4. Process the response based on type:
   - `Page`: Navigate to new page (full refresh)
   - `Update`: Display success (or do nothing)
   - `Fragment`: Update the target element's innerHTML

**Example JavaScript** (to be added):
```javascript
function handleDrafterEvent(event, url, target) {
    event.preventDefault();
    
    const formData = new FormData(event.target.form);
    
    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === 'fragment') {
            document.querySelector(data.target).innerHTML = data.content;
        } else if (data.type === 'update') {
            // Success - no visual feedback needed
        } else if (data.type === 'page') {
            // Full page navigation
            window.location.href = url;
        }
    });
}
```

## Implementation Phases

### Phase 1: Core Types (Current Implementation)
- ✓ Define `Update` and `Fragment` classes
- ✓ Update server to handle these return types
- ✓ Server-side JSON response generation

### Phase 2: Event Handler Parameters
- Add `on_click`, `on_change`, etc. parameters to components
- Generate unique routes for event handlers
- Add data attributes to HTML elements for event binding

### Phase 3: Client-Side JavaScript
- Add JavaScript to intercept events
- Implement AJAX request handling
- Implement response processing for Update/Fragment

### Phase 4: Advanced Features
- Debouncing for high-frequency events (e.g., `on_input`)
- Loading indicators during async operations
- Error handling and user feedback
- Event handler validation

## Design Considerations

### 1. State Management
**Question**: How do we ensure state consistency when multiple events fire quickly?

**Solutions**:
- Server-side request queuing
- Client-side debouncing for rapid events
- Optimistic UI updates with rollback capability
- Version tracking for state updates

### 2. Error Handling
**Question**: What happens when an event handler fails?

**Solutions**:
- Return error response type: `{"type": "error", "message": "..."}`
- Display error messages in a designated error container
- Fallback to full page refresh on critical errors
- Detailed error logging on server side

### 3. Progressive Enhancement
**Question**: Should the site work without JavaScript?

**Solutions**:
- Provide fallback to full page refresh for event handlers
- Use standard form submissions as backup
- Detect JavaScript availability and adjust UI accordingly
- Clear documentation about JavaScript requirements

### 4. Testing
**Question**: How do we test event handlers effectively?

**Solutions**:
- Unit tests for handler functions
- Integration tests using Selenium/Splinter
- Mock AJAX responses for client-side testing
- Test both JavaScript-enabled and disabled scenarios

### 5. Performance
**Question**: How do we prevent performance issues with many event handlers?

**Solutions**:
- Event delegation for repeated elements
- Lazy loading of event handlers
- Caching of frequently accessed state
- Minimize DOM manipulation in Fragment updates

### 6. Security
**Question**: How do we prevent malicious event handler calls?

**Solutions**:
- CSRF token validation for all AJAX requests
- Rate limiting on event handler endpoints
- Input validation and sanitization
- Session verification for state updates

### 7. Routing
**Question**: How do we generate routes for event handlers?

**Solutions**:
- Auto-generate internal routes based on function name
- Use special prefix (e.g., `/__event/<handler_name>`)
- Store handler registry on server
- Pass handler identifier in event data

### 8. Backwards Compatibility
**Question**: Will existing Drafter applications continue to work?

**Solutions**:
- Event handlers are optional parameters
- Existing Button/form behavior unchanged when no handler specified
- Page return type continues to work as before
- Gradual migration path for existing applications

### 9. Multiple Fragments
**Question**: Can we update multiple page sections in one response?

**Solutions**:
- Return array of Fragments: `[Fragment(...), Fragment(...)]`
- Use MultiFragment response type
- Support CSS selector lists in target parameter
- Consider performance implications

### 10. Animation and Transitions
**Question**: How do we handle smooth transitions when updating fragments?

**Solutions**:
- Add CSS classes before/after updates
- Support transition callbacks in Fragment
- Use CSS transitions for fade in/out
- Optional animation library integration

### 11. Event Handler Arguments
**Question**: How do we pass additional arguments to event handlers?

**Solutions**:
- Use Argument components like with Buttons
- Support data attributes on elements
- Pass event context (e.g., which checkbox was clicked)
- Serialize form state automatically

### 12. Nested Components
**Question**: How do event handlers work with nested components?

**Solutions**:
- Event bubbling and capturing support
- Parent-child event coordination
- Prevent event propagation when needed
- Clear component hierarchy

## Event Types Reference

### Mouse Events
- `on_click`: Element is clicked
- `on_dblclick`: Element is double-clicked
- `on_mousedown`: Mouse button is pressed
- `on_mouseup`: Mouse button is released
- `on_mouseover`: Mouse pointer enters element
- `on_mousemove`: Mouse pointer moves within element
- `on_mouseout`: Mouse pointer leaves element
- `on_mouseenter`: Mouse pointer enters element (no bubbling)
- `on_mouseleave`: Mouse pointer leaves element (no bubbling)

### Keyboard Events
- `on_keydown`: Key is pressed down
- `on_keyup`: Key is released
- `on_keypress`: Key is pressed (deprecated but still used)

### Form Events
- `on_change`: Value changes (for inputs, selects)
- `on_input`: Value changes (every keystroke for inputs)
- `on_submit`: Form is submitted
- `on_reset`: Form is reset
- `on_focus`: Element gains focus
- `on_blur`: Element loses focus
- `on_select`: Text is selected

### Other Events
- `on_load`: Element/page has loaded
- `on_unload`: Page is unloading
- `on_resize`: Element/window is resized
- `on_scroll`: Element is scrolled
- `on_error`: Error occurs during loading
- `on_abort`: Loading is aborted

## Example Use Cases

### Use Case 1: Live Search
```python
@route
def index(state: State) -> Page:
    return Page(state, [
        "Search:",
        TextBox("query", on_input=search),
        Div(id="results", content=["Enter search term"])
    ])

@route
def search(state: State, query: str) -> Fragment:
    results = state.database.search(query)
    return Fragment(
        state=state,
        target="#results",
        content=[NumberedList(results)]
    )
```

### Use Case 2: Like Counter
```python
@route
def show_post(state: State) -> Page:
    return Page(state, [
        "Post content here",
        Button("Like", on_click=like_post),
        Span(id="like-count", content=[f"Likes: {state.likes}"])
    ])

@route
def like_post(state: State) -> Fragment:
    state.likes += 1
    return Fragment(
        state=state,
        target="#like-count",
        content=[f"Likes: {state.likes}"]
    )
```

### Use Case 3: Form Validation
```python
@route
def signup(state: State) -> Page:
    return Page(state, [
        "Username:",
        TextBox("username", on_blur=validate_username),
        Span(id="username-error"),
        Button("Submit", register)
    ])

@route
def validate_username(state: State, username: str) -> Fragment:
    if len(username) < 3:
        message = "Username too short"
    elif username in state.taken_usernames:
        message = "Username taken"
    else:
        message = "✓"
    
    return Fragment(
        state=state,
        target="#username-error",
        content=[message]
    )
```

### Use Case 4: Cascading Dropdowns
```python
@route
def form(state: State) -> Page:
    return Page(state, [
        "Country:",
        SelectBox("country", state.countries, on_change=load_cities),
        "City:",
        SelectBox("city", state.cities, id="city-select")
    ])

@route
def load_cities(state: State, country: str) -> Fragment:
    state.cities = state.database.get_cities(country)
    return Fragment(
        state=state,
        target="#city-select",
        content=[SelectBox("city", state.cities)]
    )
```

## Migration Path

For existing Drafter applications:

1. **No changes required** - Applications continue to work as before
2. **Opt-in enhancement** - Add event handlers gradually to improve UX
3. **Test incrementally** - Test each new event handler independently
4. **Fallback support** - Ensure graceful degradation without JavaScript

## Conclusion

This event system design provides a flexible, powerful way to create interactive web applications in Drafter while maintaining the simplicity and educational focus of the framework. The phased implementation allows for incremental development and testing, while the comprehensive list of design considerations ensures we build a robust, production-ready system.

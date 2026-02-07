# CurrentLocation Component - Implementation Notes

## Overview

The `CurrentLocation` component provides browser geolocation integration for Drafter applications. It handles the complete permissions workflow and provides location data as a `Location` dataclass to route functions.

## Files Created/Modified

### New Files

1. **`src/drafter/components/geolocation.py`**
    - `Location` dataclass: Holds geolocation data with status, coordinates, and metadata
    - `CurrentLocation` component: Form component that requests and displays location

2. **`examples/geolocation_demo.py`**
    - Example application demonstrating the geolocation component

### Modified Files

1. **`src/drafter/components/__init__.py`**
    - Added imports and exports for `CurrentLocation` and `Location`

2. **`src/drafter/router/routes.py`**
    - Extended `try_special_conversion()` to handle `Location` type conversion from JSON

## How It Works

### 1. Component Rendering

The `CurrentLocation` component:

- Renders a div with data attributes for the field name
- Includes a hidden input field to store JSON-serialized location data
- Provides initial UI state (prompt button)
- Injects JavaScript and CSS via the `AssetBundle` mechanism

### 2. JavaScript Geolocation Handler

The bundled JavaScript:

- Initializes on page load and after dynamic content updates
- Checks browser support for geolocation API
- Checks existing permissions (if Permissions API available)
- Handles button click to request permission
- Updates UI based on permission/location status
- Stores location data as JSON in the hidden input field

### 3. Route Parameter Injection

When a route function has a `Location` parameter:

- The form submits with the hidden input containing JSON location data
- Router's `try_special_conversion()` detects the `Location` type
- JSON is parsed and converted to a `Location` dataclass instance
- The Location object is passed to the route function

## Visual States

The component displays different UI based on status:

1. **prompt** (default): "Use my location" button with explanation
2. **pending**: Spinner with "Waiting for permission..." message
3. **denied**: Warning icon with "Location blocked" and help link
4. **granted**: Success icon with "Location available ✓" (optionally shows coordinates)
5. **error**: Error icon with descriptive error message
6. **unavailable**: Info icon when geolocation API not supported

## Incomplete/Missing Features

### 1. **Component Nesting in RenderPlan** ⚠️ MAJOR GAP

**Current Issue**: The component uses `kind="raw"` with raw HTML strings instead of properly nested child components.

**Why**: The `Component` class doesn't provide a clear API for creating nested child components programmatically. There's no equivalent to `Component.create_simple_tag()` or similar helper.

**Impact**: The component works, but:

- Child elements are generated as raw HTML strings
- Manual attribute escaping is required via custom `_render_attributes()` method
- Less composable than using proper Component hierarchies
- Harder to test individual child elements

**Suggested Fix**: Add a Component API for programmatic child creation:

```python
# Proposed API
child = Component.create_element(
    "button",
    attributes={"type": "button", "class": "..."},
    children=["📍 Use my location"]
)
```

Or support dict-based child specification in RenderPlan:

```python
RenderPlan(
    kind="tag",
    tag_name="div",
    children=[
        {"tag": "input", "attrs": {...}, "self_closing": True},
        {"tag": "button", "attrs": {...}, "children": ["text"]}
    ]
)
```

### 2. **Asset Lifecycle Management** ⚠️ POTENTIAL ISSUE

**Current Issue**: JavaScript is injected every time the component renders. For Fragment updates, this could lead to multiple initializations.

**Current Workaround**: JavaScript uses `window.addEventListener('drafter:content-updated', initGeolocation)` to re-initialize on dynamic updates.

**Potential Problem**:

- If the same component is rendered multiple times on the same page, JS/CSS assets are deduplicated by the Renderer (using sets)
- However, event listeners might accumulate without cleanup
- The initialization function is idempotent for now, but this should be more robust

**Suggested Fix**:

- Add lifecycle hooks for component JS (mount/unmount)
- Use a singleton pattern for geolocation managers
- Provide a way to register JS that should only run once per component instance

### 3. **Permission State Persistence** ℹ️ ENHANCEMENT

**Current Gap**: Permission state is not persisted across page navigations.

**Impact**: If user grants permission and navigates to another route, returning to a page with `CurrentLocation` requires checking permission again (though this happens automatically if granted).

**Enhancement Idea**: Store granted permission state in SiteState or browser localStorage so the component can immediately show "granted" status without needing to re-query the API.

### 4. **Continuous Location Tracking** ℹ️ FEATURE REQUEST

**Current Limitation**: Uses `getCurrentPosition()` for a one-time location read.

**Enhancement Idea**: Add `continuous=True` parameter to use `watchPosition()` for real-time location updates. This would require:

- WebSocket or polling mechanism to update server-side state
- Callback mechanism in the component
- More sophisticated state management

### 5. **Testing Infrastructure** ⚠️ GAP

**Current Gap**: No unit tests or integration tests for the geolocation component.

**Challenges**:

- Browser APIs need to be mocked
- JavaScript execution requires a browser environment or JS testing framework
- Component rendering needs to be tested with Renderer

**Suggested Fix**:

- Add Python unit tests for `Location` dataclass and component initialization
- Add JavaScript tests using Jest or similar for geolocation handler
- Add integration tests using Playwright or Selenium for full workflow

### 6. **Error Handling Improvements** ℹ️ ENHANCEMENT

**Current**: Basic error messages displayed in UI

**Enhancements**:

- Provide more detailed browser-specific instructions for enabling location
- Add retry mechanism for timeout errors
- Allow custom error message overrides via component parameters
- Log errors to server-side monitoring

### 7. **Accessibility** ℹ️ ENHANCEMENT

**Current**: Basic semantic HTML with button elements

**Enhancements Needed**:

- Add ARIA labels and roles for screen readers
- Ensure keyboard navigation works for all interactive elements
- Add focus management for dynamic state changes
- Provide text alternatives for icon-only indicators

### 8. **Configuration Options** ℹ️ FEATURE REQUEST

**Current**: Hardcoded geolocation options (enableHighAccuracy=True, timeout=10000)

**Enhancement**: Add component parameters:

```python
CurrentLocation(
    "location",
    high_accuracy=True,
    timeout=10000,
    max_age=0,
    show_coordinates=True,
    show_accuracy=True,
    auto_request=False  # Don't show button, request immediately
)
```

### 9. **Styling Customization** ℹ️ ENHANCEMENT

**Current**: Fixed CSS styles bundled with component

**Enhancement**:

- Allow CSS class overrides via component parameters
- Support theme integration with existing Drafter themes
- Provide CSS custom properties for easier customization

### 10. **Documentation** ℹ️ TODO

**Current**: Only docstrings and this implementation note

**Needed**:

- User-facing documentation in Drafter docs
- API reference for `Location` dataclass
- Examples showing different use cases (maps, distance calculations, etc.)
- Troubleshooting guide for common browser permission issues

## Testing the Component

Run the example:

```powershell
uv run examples\geolocation_demo.py
```

Expected behavior:

1. Initial page shows "Use my location" button
2. Clicking button triggers browser permission prompt
3. Granting permission shows coordinates (if `show_coordinates=True`)
4. Submitting form passes `Location` object to route function
5. Location data is displayed on result page

## API Usage

### Basic Usage

```python
from drafter import *

@route
def index(state):
    return Page(state, [
        Header("Where are you?"),
        CurrentLocation("user_loc"),
        Button("Submit", process)
    ])

@route
def process(state, user_loc: Location):
    if user_loc.status == "granted":
        return Page(state, [
            Header(f"You are at {user_loc.lat}, {user_loc.lon}")
        ])
    else:
        return Page(state, [Header("Location not available")])
```

### With Coordinates Display

```python
CurrentLocation("location", show_coordinates=True)
```

### Location Dataclass

```python
@dataclass
class Location:
    status: "unavailable" | "prompt" | "granted" | "denied" | "pending" | "error"
    message: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    accuracy: Optional[float]  # meters
    altitude: Optional[float]  # meters
    heading: Optional[float]   # degrees
    speed: Optional[float]     # m/s
    timestamp: Optional[float] # Unix timestamp
```

## Summary

The `CurrentLocation` component is **functional** but has several areas where the Drafter framework could be extended to support more advanced component development:

1. **Most Critical**: Better API for creating nested child components programmatically
2. **Important**: Asset lifecycle management and cleanup
3. **Nice to Have**: Enhanced features like continuous tracking, better error messages, accessibility improvements

The implementation works around current limitations by using raw HTML generation, which is pragmatic but not ideal for maintainability and composability.

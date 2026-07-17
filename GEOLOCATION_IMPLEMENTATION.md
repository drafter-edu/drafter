# CurrentLocation Component - Implementation Notes

## Overview

The `CurrentLocation` component provides browser geolocation integration for Drafter applications. It handles the complete permissions workflow and provides location data as a `Location` dataclass to route functions.

It follows the same architecture as the `Timer` component: the Python side is a lean declarative component that renders a custom element, and all browser behavior lives in the JS implementation.

## Files

1. **`src/drafter/components/geolocation.py`** (Python side)
    - `Location` dataclass: Holds geolocation data with status, coordinates, and metadata
    - `CurrentLocation` component: Renders a `<drafter-current-location>` custom element and declares a `ComponentContract` (registered in `COMPONENT_CONTRACT_REGISTRY`) describing the `locate` event it emits

2. **`js/src/components/geolocation.tsx`** (JS side)
    - `drafter-current-location` custom element extending `DrafterHTMLElement`
    - Implements the permission workflow, status UI, and form value updates
    - Loaded via `js/src/components/registry.ts`; styles live in `js/src/css/default.css`

3. **`src/drafter/router/parameters/conversion.py`** (conversion)
    - `convert_location` is registered in the shared `CONVERTER_REGISTRY` and converts JSON strings or dicts into `Location` instances (it imports `Location` lazily to avoid a component→router import cycle)

4. **`examples/geolocation_demo.py`**
    - Example application demonstrating the geolocation component

## How It Works

### 1. Component Rendering

The Python `CurrentLocation` renders only:

```html
<drafter-current-location name="user_location" show-coordinates="True"
    data--drafter-handlers='{"locate": "route_name"}'>
</drafter-current-location>
```

The `data--drafter-handlers` attribute appears when `on_locate=` is given; the bridge (`src/drafter/bridge/events.py`) uses it to dispatch the `locate` event to a route.

### 2. The Custom Element

When connected, the element builds its own children:

- A hidden `<input type="hidden" name="...">` carrying the JSON-encoded location, marked with `data-transform="json-decode"` so the bridge decodes it into a dict before the router sees it
- A status area that shows the current visual state (prompt button, spinner, granted/denied/error messages)

It checks the Permissions API for an existing grant, requests the position on button click, and dispatches a `locate` `CustomEvent` (detail: flattened `Location` fields) when a position or failure is resolved. The emitted payload must match `CurrentLocation.CONTRACT` on the Python side.

### 3. Route Parameter Conversion

When a route function has a parameter matching the component's `name`:

- The form submits the hidden field; the bridge JSON-decodes it (via `data-transform`) and tags it with `form_field` provenance
- The router's parameter pipeline (`src/drafter/router/parameters/`) binds it to the signature
- If the parameter is annotated `Location`, `convert_location` in the `CONVERTER_REGISTRY` builds the dataclass; malformed data becomes `Location(status="error", ...)` rather than a crash
- Untyped parameters receive the decoded dict as-is

With `on_locate=`, the event detail fields (`status`, `lat`, `lon`, ...) also enter the payload as `event_detail` values, so an event route can take e.g. `def moved(state, lat: float, lon: float)` directly.

## Visual States

1. **prompt** (default): "Use my location" button with explanation
2. **pending**: Spinner with "Requesting permission..." message
3. **denied**: Warning icon with "Location access denied" and help button
4. **granted**: Success icon with "Location available" (optionally shows coordinates)
5. **error**: Error icon with descriptive error message
6. **unavailable**: Info icon when geolocation API not supported

The hidden field always holds a valid JSON location (starting as `{"status": "prompt", ...}`), so submitting before granting still produces a meaningful `Location`.

## Testing

- `js/src/__tests__/geolocation.test.ts`: jsdom unit tests for the custom element (mocked `navigator.geolocation`)
- `tests/components/test_components.py`: repr round-trip snippets for `CurrentLocation`
- `tests/test_router_parameters.py` (`TestLocationConversion`): conversion of JSON/dict payloads into `Location`

Run the example manually:

```powershell
uv run examples\geolocation_demo.py
```

## Possible Enhancements

- **Permission state persistence**: Remember a granted permission across page navigations (localStorage or state) to skip re-querying.
- **Continuous tracking**: A `continuous=True` option using `watchPosition()` with repeated `locate` events.
- **Configuration options**: Expose `enableHighAccuracy`, `timeout`, `maximumAge`, and an `auto_request` mode as component parameters.
- **Accessibility**: ARIA live-region announcements for status changes; text alternatives for icon-only indicators.
- **Custom messages**: Allow overriding the status messages (also relevant for i18n).

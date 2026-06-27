# Hybrid Components

A *hybrid component* is a Drafter component whose visual behavior and
interactivity are split across two layers:

- **Python layer** — a `Component` subclass that describes what HTML to emit
  and which routes to call when browser events fire.
- **JavaScript layer** — a
  [Custom Element](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_custom_elements)
  (`customElements.define`) that owns the DOM, manages state, and dispatches
  typed `CustomEvent`s.

This is the right pattern whenever a component needs to run non-trivial,
time-sensitive, or asynchronous logic in the browser (e.g. timers, sensor
APIs, real-time data streams) but still wants to surface the results to a
Python route.

---

## How the two layers communicate

### 1. Configuration flows Python → HTML attributes

The Python `Component` class serialises its fields to HTML attributes exactly
like any other Drafter component.  The custom element reads those attributes
in `connectedCallback`.

```python
# Python: renders <drafter-timer duration="4000" rate="500">
Timer(duration=4000, rate=500, on_finish=beep)
```

```typescript
// TypeScript: reads attributes in connectedCallback
connectedCallback() {
    const duration = parseInt(this.getAttribute("duration") || "1000", 10);
    const rate     = parseInt(this.getAttribute("rate")     || "1000", 10);
}
```

### 2. Event handlers are serialised as a JSON attribute

Any component argument marked `is_event=True` in `ARGUMENTS` is converted to
an entry in the `data--drafter-handlers` JSON attribute instead of a plain
HTML attribute.  Each key is the event name; each value is the route URL.

```html
<!-- on_finish=beep, on_tick=tick_route rendered as: -->
<drafter-timer
    duration="4000"
    data--drafter-handlers='{"finish": "beep", "tick": "tick_route"}'
/>
```

The JavaScript helper `getHandlers(element)` deserialises this map:

```typescript
const DRAFTER_EVENT_HANDLER = "data--drafter-handlers";
function getHandlers(element: HTMLElement): Record<string, string> {
    const raw = element.getAttribute(DRAFTER_EVENT_HANDLER);
    return raw ? JSON.parse(raw) : {};
}
```

### 3. Browser events trigger route navigation

When something interesting happens (timer fires, location granted, …) the
custom element dispatches a `CustomEvent` on itself.  Drafter's Python-side
`EventManager.mount_event_handlers` is already listening for any event whose
name appears in the `data--drafter-handlers` map; it picks up the event and
calls `do_navigation` with the matching route URL.

```typescript
// Custom element fires the event:
this.dispatchEvent(new CustomEvent("finish", { detail: { duration } }));
```

### 4. Event detail fields become route kwargs

`EventManager.get_all_event_data` merges the `event.detail` object into the
request kwargs alongside any form data.  Every key in `detail` is passed as a
keyword argument to the route function.

```python
@route
def beep(state: State):                       # no detail fields needed
    ...

@route
def tick(state: State, remaining: int):       # "remaining" comes from detail
    ...
```

---

## Implementing a hybrid component

### Python side

```python
from dataclasses import dataclass
from typing import Optional
from drafter.components.page_content import Component, ComponentArgument, UrlOrFunction

@dataclass(repr=False)
class MyWidget(Component):
    # 1. Custom element tag name registered in JS
    tag = "my-widget"

    # 2. Fields (rendered as HTML attributes)
    interval: int
    on_tick: Optional[UrlOrFunction] = None

    # 3. Event names the JS element can fire
    EXTRA_SUPPORTED_EVENTS = ["tick"]

    # 4. Rename Python names → HTML attribute names where needed
    RENAME_ATTRS = {}   # e.g. {"my_field": "my-field"}

    # 5. Attributes that the renderer should treat as real HTML attrs,
    #    not as CSS style properties
    KNOWN_ATTRS = ["interval"]

    # 6. ARGUMENTS drives both __repr__ and get_attributes
    ARGUMENTS = [
        ComponentArgument("interval", "positional"),
        ComponentArgument("on_tick", "keyword", None, is_event=True),
    ]

    def __init__(self, interval: int, on_tick=None, **kwargs):
        self.interval = interval
        self.on_tick  = on_tick
        self.extra_settings = kwargs
```

Key points:

| Class attribute | Purpose |
|---|---|
| `tag` | Must match the string passed to `customElements.define` in JS |
| `EXTRA_SUPPORTED_EVENTS` | Event names that `_handle_event` will accept (without the `on_` prefix) |
| `KNOWN_ATTRS` | Attributes listed here are rendered as `attr="value"`; anything *not* listed (and not a `data-*` attr) is treated as a CSS style |
| `RENAME_ATTRS` | Maps Python field name → HTML attribute name (use for kebab-case names) |
| `is_event=True` on a `ComponentArgument` | Causes the value to be written to `data--drafter-handlers` rather than as a plain attribute |

### JavaScript side

Add a new file under `js/src/components/` and import it from `registry.ts`.

```typescript
// js/src/components/my-widget.tsx
const DRAFTER_EVENT_HANDLER = "data--drafter-handlers";
function getHandlers(el: HTMLElement): Record<string, string> {
    const raw = el.getAttribute(DRAFTER_EVENT_HANDLER);
    return raw ? JSON.parse(raw) : {};
}

class MyWidget extends HTMLElement {
    private timerId: number | null = null;

    connectedCallback() {
        const interval = parseInt(this.getAttribute("interval") || "1000", 10);
        const handlers = getHandlers(this);

        this.timerId = window.setInterval(() => {
            if (handlers["tick"]) {
                this.dispatchEvent(
                    new CustomEvent("tick", { detail: { elapsed: Date.now() } })
                );
            }
        }, interval);
    }

    disconnectedCallback() {
        if (this.timerId !== null) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
    }
}

customElements.define("my-widget", MyWidget);
```

```typescript
// js/src/components/registry.ts  (add one line)
import "./my-widget";
```

---

## The Timer component — reference implementation

`Timer` (`src/drafter/components/timer.py` + `js/src/components/timer.tsx`) is
the canonical example of a hybrid component.

| Python parameter | HTML attribute | JS behavior |
|---|---|---|
| `duration` | `duration` | Total countdown in ms |
| `on_finish` | encoded in `data--drafter-handlers["finish"]` | Route called when timer expires |
| `show` | `show` | *Not yet implemented in JS* — label always shown |
| `controls` | `controls` (boolean) | Adds pause/restart buttons |
| `persistent` | `persistent` | *Not yet implemented in JS* — timer resets on navigation |
| `rate` | `rate` | Interval between ticks in ms |
| `on_tick` | encoded in `data--drafter-handlers["tick"]` | Route called on each tick; receives `remaining` and `duration` |

### Known API gaps in Timer

The following Timer features are declared on the Python side but not yet
implemented in the JavaScript custom element:

1. **`show` attribute** — the countdown label is always visible regardless of
   `show=False`.
2. **`persistent` attribute** — the timer always resets when the page HTML is
   replaced.  A persistent timer would need to survive page re-renders by
   storing start time in `sessionStorage` or similar.
3. **`attributeChangedCallback`** — `observedAttributes` lists `duration` and
   `rate`, but no `attributeChangedCallback` method is defined, so changing
   these attributes after render has no effect.
4. **`Clock` component** — the Python `Clock` class (ticking *up* via
   `setInterval`) is a stub: it has no `tag`, no `ARGUMENTS`, and no
   corresponding JavaScript custom element.

---

## The CurrentLocation component

`CurrentLocation` (`src/drafter/components/geolocation.py` +
`js/src/components/geolocation.tsx`) demonstrates a hybrid component that
bridges a browser sensor API (Geolocation) to both form-submission and
event-driven workflows.

### Events

| Python parameter | Event name | Detail fields passed to route |
|---|---|---|
| `on_grant` | `grant` | `lat`, `lon`, `accuracy`, `altitude`, `heading`, `speed`, `timestamp`, `status`, `message` |
| `on_deny` | `deny` | `status`, `message` |
| `on_error` | `error` | `status`, `message` |
| `on_unavailable` | `unavailable` | `status` |

### Form-submission workflow

When no event callbacks are provided, `CurrentLocation` works like any other
form widget.  The custom element creates a hidden `<input>` that stores
JSON-serialised location data.  When the user submits the form, the router
converts that JSON to a `Location` dataclass via `try_special_conversion`:

```python
CurrentLocation("loc")
Button("Submit", process)

@route
def process(state, loc: Location):
    if loc.status == "granted":
        print(loc.lat, loc.lon)
```

### Event-driven workflow

With callback parameters, the route is called as soon as the browser responds,
without requiring a button press:

```python
CurrentLocation("loc", on_grant=location_ready)

@route
def location_ready(state, lat: float, lon: float, accuracy: float):
    ...
```

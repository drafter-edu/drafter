# Drafter v2 Architecture

This document describes the architecture as it is actually implemented, with design intent that has
not yet been built explicitly marked **[PLANNED]**. When a name in this document and a name in the
code disagree, the code wins - please update this document rather than "fixing" the code to match it.

## Organization

When you run a Drafter program that has a `start_server` call, the logic in `src/drafter/launch.py`
dispatches three ways (`launch.py`, `start_server` dispatch):

1. **Web mode** (`is_web()` is true - we are running inside Skulpt or Pyodide in the browser):
   `run_client_bridge` is called to wire up the `ClientBridge` and `ClientServer`.
2. **Compile mode** (`system.bootstrap.mode == "compile_site"`): `compile_site` (in
   `src/drafter/builder/build.py`) generates static HTML/CSS/JS files that can be deployed to any
   static hosting service.
3. **App mode** (everything else - normal CPython): `serve_app_once` (in
   `src/drafter/app/app_server.py`) starts a local development server.

The dev server and the builder are function-based modules: `make_app()`/`serve_app_once()` build and run a **Starlette**
application served by **uvicorn**, and `compile_site()` performs the static build. The similarly
named `AppServerConfiguration` and `AppBuilderConfiguration` classes are configuration dataclasses
only (see Configuration below), with shared fields in `AppCommonConfiguration`.

In app mode, the server serves a single "True Page" containing a div with the Drafter root. The page
sets up Skulpt/Pyodide plus a hot-reload WebSocket connection back to the dev server, and then loads
and runs the user's code in the browser runtime. This effectively runs the program twice: first
"server side" in CPython (starting the server, running unit tests, printing output), then "client
side" in Skulpt/Pyodide, where the user's application actually runs. The default engine is
**Pyodide** (`AppCommonConfiguration.engine = "pyodide"`); Skulpt remains a semi-supported alternative
via `--engine skulpt`. Skulpt is legacy: its code (`js/src/skulpt_bridge/`) and Jest project
(`npm run test:skulpt`, currently known-failing) are outside the regular validation baseline, and
should not be modified or "fixed" as a side effect of other work (see AGENTS.md).

Hot reload: the dev server exposes a WebSocket route backed by `ReloadHub` and a `watchfiles`
watcher (`src/drafter/app/watcher.py`). The watcher distinguishes "full reload" from "restart
student code" messages, but the Skulpt client currently handles both with `location.reload()`; the
Pyodide client receives the restart message through `startPyodideAppServerSession`.

If the user runs the program directly in Skulpt/Pyodide, then reaching `start_server` triggers
`run_client_bridge` (`src/drafter/bridge/bridger.py`), which sets up the `ClientBridge` and the main
`ClientServer`. The `ClientServer` is **not** a real server; it is a class that handles requests
from the `ClientBridge` and generates responses.

- The `ClientBridge` (`src/drafter/bridge/client_bridge.py`) populates the DOM, tracks user
  interactions, and sends requests from the client side.
- The `ClientServer` (`src/drafter/client_server/client_server.py`) processes requests, manages
  state, and generates responses on the "server" side.

The `ClientBridge` is deliberately stupid about the site's contents; as much logic as possible is
pushed into the `ClientServer`. The `ClientServer` sends information to the `ClientBridge`, which
performs updates on the page (updating page content, adding new JS/CSS, notifying the debug panel,
etc.).

The default server instance is the module-level global `MAIN_SERVER` in
`src/drafter/client_server/commands.py`. It is created **lazily** by `get_main_server()` on first
access (not eagerly at import). A multi-instance registry (`_SERVER_REGISTRY`, `register_server`,
`configure_instance`, `instance_root`) supports embedding multiple independent Drafter apps on one
page (e.g., in documentation via iframes/shadow DOM); `configure_instance` clears `MAIN_SERVER` so
each instance gets its own server and event bus. See "Multi-Instance Embedding" below.

## DOM Structure

The single source of truth for element ids is `DRAFTER_TAG_IDS` and `SITE_HTML_TEMPLATE` in
`src/drafter/site/site.py`. The ids all use a trailing `--` suffix:

- `drafter-root--` - the top-level div that contains ALL Drafter content (except top-level script
  tags needed to load the true initial page). The site template is injected into it.
- `drafter-site--` - a div containing the entire site.
- `drafter-form--` - a **`<form>` tag** , a direct child of the site. It wraps the frame,
  so all form fields inside the page content participate in one form.
- `drafter-frame--` - a div inside the form that makes the app look like it is in a browser window.
  The frame chrome is only visible in development mode; in deployed mode only its content shows.
- `drafter-header--`, `drafter-body--`, `drafter-footer--` - divs inside the frame. Header and
  footer are hidden in deployed mode (`drafter_deploy.css`). The header holds the site title and
  quick links (reset state, about page, edit source); the footer holds the current route/status and
  the persisted-components list.
- `drafter-debug--` - the debug panel, a **sibling of the form** (both are children of the site).
- `drafter-persist--` - a hidden div inside the footer used to "park" persistent components (see
  Component Persistence below).
- `drafter-subtle-debug-entry--` - a mostly-hidden button that offers a debug entry point on
  deployed sites (guarded by `data-enabled`/`data-visible` attributes in `drafter_deploy.css`).
- `drafter-shadow-host--` - the host element used when the site is rendered into a shadow DOM
  (multi-instance embedding).

Padding is provided by class-only divs `drafter-padding-h--` (wrapping the form horizontally inside
the site) and `drafter-padding-v--` (above/below the frame inside the form). Other notable classes:
`drafter-theme--`, `drafter-debug-css--`, `drafter-non-debug-css--`, `drafter-precompiled-headers--`
(marker classes for injected style/script tags) and the visibility toggles `drafter-hidden--` /
`drafter-body-frame-hidden--`.

The structure can be summarized as:

- Root > Site > Form > Frame > Header
- Root > Site > Form > Frame > Body > (Page's content goes here)
- Root > Site > Form > Frame > Footer > Persist
- Root > Site > DebugInfo (sibling of the Form)

```
┌─True─Site─────────────────────────────────────────────┐
│ ┌True─Head──────────────────────────────────────────┐ │
│ └───────────────────────────────────────────────────┘ │
│ ┌True─Body──────────────────────────────────────────┐ │
│ │┌─Root────────────────────────────────────────────┐│ │
│ ││┌─Site──────────────────────────────────────────┐││ │
│ │││ ┌─Padding-h─────────────────────────────────┐ │││ │
│ │││ └───────────────────────────────────────────┘ │││ │
│ │││ ┌─Form──────────────────────────────────────┐ │││ │
│ │││ │ ┌─Padding-v─────────────────────────────┐ │ │││ │
│ │││ │ └───────────────────────────────────────┘ │ │││ │
│ │││ │ ┌─Frame─────────────────────────────────┐ │ │││ │
│ │││ │ │ ┌─Header───────────────────────────┐  │ │ │││ │
│ │││ │ │ └──────────────────────────────────┘  │ │ │││ │
│ │││ │ │ ┌─Body─────────────────────────────┐  │ │ │││ │
│ │││ │ │ └──────────────────────────────────┘  │ │ │││ │
│ │││ │ │ ┌─Footer───────────────────────────┐  │ │ │││ │
│ │││ │ │ └──────────────────────────────────┘  │ │ │││ │
│ │││ │ └───────────────────────────────────────┘ │ │││ │
│ │││ │ ┌─Padding-v─────────────────────────────┐ │ │││ │
│ │││ │ └───────────────────────────────────────┘ │ │││ │
│ │││ └───────────────────────────────────────────┘ │││ │
│ │││ ┌─Padding-h─────────────────────────────────┐ │││ │
│ │││ └───────────────────────────────────────────┘ │││ │
│ │││ ┌─Debug─Panel───────────────────────────────┐ │││ │
│ │││ └───────────────────────────────────────────┘ │││ │
│ ││└───────────────────────────────────────────────┘││ │
│ │└─────────────────────────────────────────────────┘│ │
│ │┌─True─Scripts─Footer─────────────────────────────┐│ │
│ │└─────────────────────────────────────────────────┘│ │
│ └───────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

When page content is rendered, it replaces the content of the body (inside the form) without
replacing the form itself.

A note on the `Site` class (`src/drafter/site/site.py`): despite the name, it is not a container of
Form/Body/DebugInfo objects. It is a small dataclass holding the current `ClientServerConfiguration`
(private `_configuration` field) that knows how to render the site frame HTML (`render()` →
`InitialSiteData`), render theme/style headers, and render an error fallback. The DOM structure
above lives in its `SITE_HTML_TEMPLATE` (and `SITE_HTML_SHADOW_DOM_TEMPLATE`).

## Request/Response Model

We use a request/response model to update page content, based around events. When the user
interacts with the page (clicks a link, submits a form, etc.), the `ClientBridge` sends a `Request`
to the `ClientServer`.

The `Request` dataclass (`src/drafter/data/request.py`) carries:

- `action`: what led to the request (e.g., `"click"`, `"back"`, `"redirect"`, `"precompilation"`).
- `url`: the URL path being requested (which matches a route function).
- `kwargs`: the merged form data (input fields, `Argument`s, uploaded files) as a dict.
- `event`: extra event information as a plain **dict** (clicked button, scroll position, etc.).
- `dom_id`, `button_pressed`, `raw_payload`, `id`: bookkeeping fields. `raw_payload` is a list of
  provenance-tagged entries (`name`/`value`/`source`/`source_detail`) that the Router uses to bind
  parameters with correct precedence.

The `ClientServer` processes the request in `do_visit` (there is no method named just `visit`):
route lookup is `get_route` (delegating to `Router.get_route`), then `execute_route` calls the route
function safely, converting exceptions into error responses. The route function is expected to
return a `ResponsePayload`. The payload gets post-processed and wrapped in a `Response`
(`src/drafter/data/response.py`) along with metadata - a symbolic `status_code` string (one of the
`STATUSES` in `drafter/data/errors.py`, not a numeric HTTP code), `errors`, `warnings`, `channels`,
`target`, `metadata`, etc. The `Response` is **always** sent back to the `ClientBridge`, even in
error cases. Think of the Payload as "the thing we will show the user," while the Response is "the
meta information for the system": error metadata rides on the Response, while the Payload might
still be a Page showing a friendly error message.

### Payloads

`ResponsePayload` (`src/drafter/payloads/payloads.py`) has these subclasses under
`src/drafter/payloads/kinds/`:

- `Fragment` - the real base payload: an HTML string injected at a `Target`.
- `Page` - subclasses `Fragment` with a predefined target (`DEFAULT_BODY_TARGET`, pointing at the
  body div with `replace=False` and `is_page_load=True`). So a Page literally *is* a Fragment with a
  predefined target location.
- `Update`, `Redirect`, `Download`.
- `SimpleErrorPage` - the last-resort error payload. **Note:** there is no `ErrorPage` payload
  class; normal error rendering goes through the system error *route* (see Error Handling), and
  `SimpleErrorPage` is only the fallback when that itself fails. (An overridable `ErrorPage` payload
  remains a TODO.)
- `Progress` - **[PLANNED]** currently an empty stub ("not yet ready"); see Streaming below.

Lifecycle methods on `ResponsePayload`:

- `verify(router, state, configuration, request)`: before being sent to the client, the payload is
  verified (required fields present, links valid, etc.).
- `render(state, configuration)`: produces the HTML, recursively rendering components and their
  children.
- `get_messages(state, configuration)`: generates additional content to run before/after the main
  content is inserted (e.g., `Fragment` emits CSS into the `"before"` channel and JS into the
  `"after"` channel).
- `format(state, representation, configuration)`: a string representation used for
  logging/debugging and test generation - `Fragment.format` actually emits an `assert_equal(...)`
  style test string, not a plain repr.
- `get_state_updates()` → `(bool, Any)`: changes the payload wants applied to the State; applied by
  the `ClientServer` after processing but before responding.
- `is_redirect()`, `get_redirect()`, `get_target(request)`: redirect detection/unpacking and target
  resolution.

### Channels

Messages between server and bridge ride on named `Channel`s of `Message`s
(`src/drafter/data/channel.py`), attached to the `Response` (`Response.channels`, with
`send`/`send_messages` helpers). Default channel names are `"before"`, `"after"`, and `"audio"`.
The bridge injects "before" content (e.g., styles) before updating the page and "after" content
(e.g., scripts) afterwards.

### Targets

The `target` parameter accepts `Target` instances (`src/drafter/payloads/target.py`) that specify
where and how content is injected. A `Target` can select by `id`, `tag`, `class_name`, raw
`selector`, `data_attribute`, `attribute`, `nth_child`, `closest`, or `within`; `all` controls
one-vs-all matches; `replace` toggles replacing the whole node vs. its children. Targets also
support actions beyond injection: `remove`, `append`, `prepend`, `before`, `after`,
`attributes_to_set`, `styles_to_set`, `class_toggles`, plus `fallback` targets and an
`is_page_load` flag. For a `Page`, the target is always the body div.

### Special Route Parameters

Route functions usually expect `state` as their first parameter. The complete set of "special"
parameter behaviors (implemented in `src/drafter/router/parameters/binding.py` and
`introspect.py`):

- `state`: injected positionally when the first parameter is literally named `state`, or when an
  arity heuristic determines the function expects exactly one more parameter than the request
  supplied.
- `_request`, `_server`, `_configuration`: framework-injected dependencies. Any parameter starting
  with an underscore (`INJECTED_PARAMETER_PREFIX = "_"`) is treated as framework-injected;
  `_request` receives the raw `Request`, `_server` the `ClientServer`, `_configuration` the current
  `ClientServerConfiguration`.
- `**kwargs`: if the function declares a var-keyword parameter, leftover unmatched form fields are
  collected into it. (A parameter merely *named* `kwargs` is not special.)
- Event data is **not** injected as a single `event` object; individual event-detail values are
  spread into the payload (tagged `source="event_detail"`) and bound by name like any other value.

**[PLANNED]** Injecting a `page: Page` object as an alternative first parameter (giving access to
the current Page including the State) is designed but not implemented.

Reentrant pages: if a route function has default parameters, the URL can be called without those
parameters and the defaults will be used (missing parameters are only an error when they have no
default). This allows reentrant URLs that can be bookmarked or shared.

### Committing Responses

The `ClientBridge.handle_response` path updates the DOM faithfully according to the `Response`:

1. Removes all page-specific content currently in place.
2. Injects "before" channel content (e.g., styles).
3. Registers the navigation callback and notifies the debug panel of the new route.
4. Updates the body content (and, on full page loads, dispatches a page-loaded event).
5. Re-mounts navigation/interaction handlers.
6. Injects "after" channel content (e.g., scripts).
7. If the payload is a redirect, `NavigationController.handle_redirect` first checks a redirect-loop
   stack (by payload repr) - a repeat aborts with a `bridge.redirect_loop_detected` error -
   otherwise it builds a new `Request("redirect", ...)` and starts over from the top.

Errors and warnings are surfaced in the debug panel via telemetry (see Telemetry).

### Streaming and Long-Running Tasks **[PLANNED]**

The design is to let route handlers `yield` `Progress` payloads which are sent to the
`ClientBridge` as they are generated, so a single request can produce multiple responses over time
(progress indicators, partial results). None of this is implemented yet: `Progress` is a stub and
the `ClientServer` has no generator handling.

## The Developer's Perspective

From the student developer's perspective, they are building a site with multiple routes. A route is
a decorated function that takes the current `State` and any relevant parameters and returns a `Page`
(or other `ResponsePayload`). The site also has metadata like title, description, language, etc.
(see `SiteInformation` in `src/drafter/config/site_information.py`).

How do users create "dynamic" route functions? They don't. Instead, they parameterize their route
functions. Dynamic behavior comes from payloads like `Fragment`, where a route is attached to a
component and triggered through an event. For example, a textbox `on_change` event doing live
validation:

```python
@route
def validate_name(state: State, name: str) -> Fragment:
    if len(name) < 3:
        return Fragment(state, "#name_validation", "Invalid")
    else:
        return Fragment(state, "#name_validation", "Valid")

@route
def index(state: State) -> Page:
    return Page(state, [
        TextBox("name_input", on_change=validate_name),
        Div("name_validation", "")
    ])
```

A URL is a string that represents a unique route function. It should follow Python function naming
conventions (lowercase letters, numbers, underscores). Eventually, we might support slashes for
things like classes or modules (which would probably translate to periods).

## State Data

Drafter organizes its functionality around route functions. A route generates a Page. Pages connect
to other routes, usually via Buttons/Links (other mechanisms include `on_change` events, timers,
etc.).

There are eight kinds of data handled in Drafter (the last two are **[PLANNED]**):

1. App `State`: the current application state, passed to route functions and tracked (with history)
   by `SiteState` (`src/drafter/history/state.py`).
2. Page Arguments: `Argument`s defined in a `Page`'s content, passed to any connecting routes. They
   are rendered as hidden input fields with the name stored **verbatim** (no prefix); the value is
   JSON-encoded and flagged for client-side decoding with a `data-transform="json-decode"`
   attribute (`src/drafter/components/links.py`). (The old design of prefixing the *name* with a
   special marker string was dropped; the leftover `JSON_DECODE_SYMBOL` constant is unused.)
3. Page Fields: form fields (text inputs, file uploads, etc.) defined in a `Page`, stored as regular
   form fields and included in the form data of any request.
4. Route Arguments: `Argument`s attached to a specific route connection, stored JSON-encoded in
   `data--drafter-arguments` (and handlers in `data--drafter-handlers`) attributes on the relevant
   DOM element (`src/drafter/components/page_content.py`).
5. Event Information: details about the triggering event, spread into the request payload as
   individual `event_detail` values (see Special Route Parameters).
6. Config Information: configuration parameters accessible via the injected `_configuration`
   parameter.
7. **[PLANNED]** Local Storage: data stored in the client's browser across sessions. (localStorage
   is currently used only for debug config overrides - there is no general storage mechanism.)
8. **[PLANNED]** Remote Storage: data stored on a server across sessions and devices.

## Summary of Execution Timeline

Fundamentally, the user writes a Python script that starts with `from drafter import *`, defines
routes, and calls `start_server(initial_state)`. This can be run three ways:

1. `python -m drafter user_script.py` (via `src/drafter/__main__.py`)
2. `drafter user_script.py` (via the `drafter = "drafter.cli:main"` entry point in `pyproject.toml`)
3. `python user_script.py`

All three work roughly the same: the package is imported, configuration is processed (from
`sys.argv`, environment variables, and/or a config file) into the `SystemConfiguration` singleton,
and then the user's code runs. For (1) and (2), `drafter.cli.main` executes the student's file via
`runpy.run_path(...)`; for (3) the student's code simply continues executing after the import.
Either way, execution eventually reaches the `start_server` call. All of this configuration logic
lives in the top-level `src/drafter/configuration.py` module (`configure_system`,
`get_system_configuration`); `launch.py` handles the actual launching/building using that
configuration, and `cli.py` basically just runs the student's file. (The old `do_main`/
`command_line.py` machinery is deprecated; `command_line.py` survives only as orphaned v1 code.)

1. Bootstrap Phase
   1. The Drafter library is imported.
   2. `configure_system()` builds the `SystemConfiguration` (stored in the module-global
      `_SYSTEM`, accessed via `get_system_configuration()`):
      1. `BootstrapConfiguration` is processed first (env vars, CLI args, config file); its `mode`
         determines whether we are in `start_server` or `compile_site` mode.
      2. The remaining configs are created and merged: `ClientServerConfiguration`,
         `AppServerConfiguration`, `AppBuilderConfiguration`, and `AppCommonConfiguration`.
2. Pre-initialization Phase
   1. `MAIN_SERVER` is *lazily* created on first `get_main_server()` call (a `ClientServer` named
      `"MAIN_SERVER"`).
3. Pre-Initialized Phase
   1. If the user ran their program directly, their code executes naturally.
   2. If the user ran `drafter ___` or `python -m drafter ___`, their code is executed via `runpy`.
4. Launch Phase
   1. `start_server(...)` merges its keyword arguments into the (static) system configuration via
      `merge_in_args`.
   2. If we're in `start_server` mode (CPython):
      1. `serve_app_once` builds and starts the Starlette app (served by uvicorn).
      2. If `prerender_initial_page` is set (default true), `precompile_server` renders the
         initial page (see First Page below).
      3. The initial True Page is served to the browser.
      4. The True Page sets up the hot-reload WebSocket connection back to the dev server.
      5. The True Page sets up the Skulpt/Pyodide environment.
      6. The True Page embeds the launch-time configuration deltas as
         `window.DRAFTER_MODIFIED_CONFIGURATION` (from `get_system_config_modifications()`,
         passed to the template as `modified_system`).
      7. The True Page executes the student's code (go to Initialization).
   3. If we're in `compile_site` mode:
      1. `compile_site` generates the static site files, including the pre-rendered initial page.
      2. The generated files can be deployed to any static hosting service.
      3. When a user visits the site, steps 4.2.5–4.2.7 happen the same way (minus the WebSocket).
5. Initialization Phase (now inside Skulpt/Pyodide)
   1. Drafter is imported.
   2. The `SystemConfiguration` singleton is initialized (including the embedded modifications).
   3. The `MAIN_SERVER` (`ClientServer`) is created on first use.
6. Initialized Phase
   1. The rest of the student's code executes, adding routes to the `MAIN_SERVER`, until it reaches
      `start_server`.
   2. `launch.py` calls `run_client_bridge` (`src/drafter/bridge/bridger.py`).
7. Configuring Phase
   1. The `ClientServer` is configured (`ClientServer.do_configuration`), which copies the default
      configuration into the current configuration on the `Site` and processes dynamic
      configuration (see Configuration below).
8. Rendering Phase
   1. The `ClientServer` renders the Site (`ClientServer.do_render`).
   2. `run_client_bridge` creates the `ClientBridge` (resolving the per-instance `DomContext` and
      registering the server for multi-instance embedding).
   3. `ClientBridge.setup_site` loads the rendered site and sets up the Debug Menu.
   4. `run_client_bridge` attaches the bridge's event handler to the `ClientServer`'s event bus
      (`server.do_listen_for_events(client_bridge.handle_server_event)`).
   5. `ClientBridge.setup_events` attaches handlers for page interactivity and page-wide navigation
      (`popstate`, `drafter-navigate`, `drafter-toggle-frame`, `drafter-toggle-debug-mode`,
      `drafter-evict-persistent`).
   6. Hotkey bindings are registered (each triggered by **Ctrl/Cmd + double-press** within
      600ms): `Q` toggles the Debug Menu, and `I` toggles between the About page (`--about`)
      and the index.
9. Starting Phase
   1. The `ClientServer` is started (`ClientServer.do_start`).
   2. The state is initialized from the initial state.
   3. Missing system routes are registered with the router (`src/drafter/router/system_routes.py`,
      defaults in `src/drafter/router/defaults/`: about, bug-report, error, index, reload, reset).
10. Started Phase
    1. The `ClientBridge` creates the initial `Request`.
    2. The `ClientBridge` initiates a visit with the initial `Request`.
11. Visiting Phase (`ClientServer.do_visit`)
    1. The `ClientServer` gets the route function (`get_route`).
    2. The `ClientServer` executes the route function (`execute_route`) and gets a Payload.
       1. Argument preparation is delegated to the `Router` (see below).
       2. The route function is executed safely; exceptions become error responses.
    3. The `ClientServer` verifies the Payload (`verify_payload`).
    4. The `ClientServer` renders the Payload to generate the new HTML (`render_payload`).
    5. The `ClientServer` formats the Payload for logging/debugging/testing (`format_payload`).
    6. The `ClientServer` updates its state based on the Payload (`handle_state_updates`).
    7. The `ClientServer` generates messages for the `ClientBridge` (`get_messages`).
    8. The `ClientServer` resolves the target (`get_target`).
    9. The `ClientServer` returns a response (`make_success_response`).
12. Committing Phase - see "Committing Responses" above.
13. Idle Phase
    1. The page is fully loaded; we wait for user interaction.
14. Navigating Phase
    1. The user triggers an event handler (clicks a button, presses back, a component event fires).
    2. The `ClientBridge` prepares a new `Request` with the relevant information.
    3. The `ClientBridge` sends the `Request` to the `ClientServer` (a "Visit").
    4. Go to (11) Visiting Phase.

The `ClientServer` tracks these phases explicitly in a `ServerPhases` state machine.

### Argument Preparation

`Router.prepare_arguments` (`src/drafter/router/routes.py`) runs a five-stage pipeline (the stages
are named in its docstring and implemented under `src/drafter/router/parameters/`):

1. **Collect**: make a fresh copy of the request kwargs, preprocess button presses
   (`preprocess_button_press` - TODO: check if this is still necessary; it retains a
   Skulpt-compatibility fallback), and gather the provenance-tagged payload entries
   (`collect_payload`).
2. **Normalize**: apply component alias mappings to payload names (`normalize_payload`).
3. **Bind**: merge payload entries with precedence (`PayloadMerger`), inspect the route function's
   signature, inject `state` and underscore-prefixed framework dependencies, and apply defaults
   (`RouteBinder.bind`).
4. **Convert**: convert bound values to their destination types via the `CONVERTER_REGISTRY`
   (happens inside binding).
5. **Diagnose**: `report_diagnostics` raises `ParameterBindingError` for missing or unconvertible
   parameters and warns about unused or colliding values (diagnostic codes in
   `router/parameters/diagnostics.py`).

Finally, `build_argument_representation` produces a string representation of the arguments for
logging/debugging.

## History and Navigation

We hijack the browser's back/forward buttons. `BrowserHistory` (`src/drafter/bridge/history.py`)
pushes History API entries containing `{request_id, url, kwargs}` plus a `?route=` query parameter.
On `popstate`, the entry is converted back into a `Request("back", url, kwargs, ...)` and replayed
through the normal visit flow. State history itself is kept in memory on the server side in
`SiteState` (`current`, `history`, `initial`).

Known gaps **[PLANNED]**:

- Uploaded files and full form data are not yet restored on back/forward (`TODO: Restore the data dictionary` in `history.py`); uploads live only in memory for the request that carried them.
- There is no per-tab session ID (e.g., in `sessionStorage`) to restore continuity after the user
  navigates away to another site and returns.
- Rather than stuffing state into `pushState` entries, the intended design is a documentId model
  where entries reference records in localStorage/IndexedDB, with a garbage-collection strategy for
  old documents. This would also handle data too large for the URL/history entry.
- A `PersistentStore` abstraction in the ClientBridge (in-memory / localStorage / IndexedDB
  backends, with server-issued store/retrieve commands) is designed but does not exist. Note: the
  existing `src/drafter/bridge/persistence.py` is *not* this - see Component Persistence.

### The First Page

When the server starts up, it creates an initial State. If `prerender_initial_page` is enabled
(default), `precompile_server` runs `do_render` + `do_start` + a synthetic
`Request("precompilation", "index", ...)` visit to produce `compiled_body` and `compiled_headers`,
which are embedded in the generated True Page template so SEO crawlers can see initial content.
When the `ClientBridge` connects, it immediately requests the index page (unless a specific other
page was requested via query arguments), which runs on the `ClientServer` to generate the real page.

### Component Persistence ("Parking")

Components marked `data-drafter-persistent` (e.g., timers, audio/video players) are "parked" into
the hidden `drafter-persist--` div when page content is swapped, and restored when a new page
includes them again (`src/drafter/bridge/persistence.py`, using `moveBefore` and media-resume
logic). This lets media keep playing and timers keep running across simulated page loads. The
debug footer lists parked components with reveal/evict controls, and the `drafter-evict-persistent`
event evicts them.

## Error and Warning Handling

Errors are represented by a single canonical dataclass, `ErrorDetails(Exception)`
(`src/drafter/data/errors.py` - note: plural), with fields `id`, `category`, `message`, `severity`,
`details`, `traceback`, `context`, `status_code`, `recoverable`. Failures are distinguished by
stable string ids (e.g., `request.route_not_found`, `request.argument_parsing_failed`,
`request.route_execution_failed`, `state.type_change`, `site.rendering_failed`,
`system.response_creation_failed`, `bridge.redirect_loop_detected`) and categories
(system/request/payload/bridge/config/runtime), not by exception subclasses.
`envelope_from_exception()` converts arbitrary exceptions.

Where errors can occur:

- Core infrastructure during initial page load (e.g., Pyodide/Skulpt setup).
- Route resolution (no matching route, argument parsing/binding errors).
- Route execution (exceptions raised in student code).

Severity varies: **errors** prevent the page from working and are shown to the user in a friendly
way; **warnings** indicate potential issues but don't prevent functioning; **debug information** is
for the developer. Errors are attached to the eventual `Response` AND published through telemetry
(`log_error`). Route/render failures short-circuit `do_visit` and return an error response
immediately; warnings are accumulated during the visit (via a transient event-bus subscription) and
attached to both success and error responses.

Error rendering: the system error route (`src/drafter/router/defaults/error.py`) renders a full
styled error `Page` with a summary, suggested fixes, and a parsed traceback that badges student-code
frames ("your code") with line numbers and source context. If the error route itself fails,
`SimpleErrorPage` is the last-resort fallback.

Where errors are shown to the user (implemented):

- The Drafter page content area - friendly, styled error pages (404s, route errors, etc.).
- The entire page, if Drafter's infrastructure fails to load - the JS engine has a presentation
  policy matrix (severity × recoverable → render-in-root / modal dialog / log-only) in
  `js/src/bridge/engine.ts`; critical non-recoverable errors render a panic view into the root.
- A modal dialog for recoverable errors (`alertDialog`).
- The debug panel, via the telemetry sink.
- The browser console (`console.error`, always).
- The original system console, as a fallback when browser console conversion fails.

**[PLANNED]**: a lightweight toast variant; a dedicated hidden error dialog (hotkey-revealed) that
dumps full request/response and stack traces on deployed sites (currently the debug panel serves
this role); writing errors/logs to a file on disk.

### Error Details

- Missing required parameter: names the parameter and route, with a "did you mean" suggestion for
  close parameter names (via `difflib.get_close_matches` in `router/parameters/binding.py`) or a
  hint about defaults. Theme names get similar suggestions in `styling/themes.py`.
- Invalid parameter type: the conversion diagnostics carry the converter's message and hint
  (including the expected type).
- Errors during a route: the error page shows the exact line number and source context within the
  student's code.
- **[PLANNED]** Unknown route: currently reports "No route found for URL: ..." with generic advice.
  It should also list the available routes and use string distance to suggest the route the user
  probably meant (the difflib machinery exists for parameters/themes; it is not yet applied to
  routes).

## Telemetry

The `EventBus` (`src/drafter/monitor/bus.py`) is a pub/sub system that lets parts of the
application communicate without tight coupling. Each `ClientServer` instance has its own bus
(`get_main_event_bus()` returns the main instance's). Topic matching supports a `"*"` wildcard and
prefix matching; events published with no subscribers are queued (bounded at 500) and replayed when
a subscriber attaches.

Telemetry records are subclasses of `TelemetryRecord` (`src/drafter/data/telemetry.py`). There is
deliberately **no envelope type**: each record carries its own `TelemetryMetadata` (source, level,
auto-incremented id, version, timestamp) and `Correlation` context
(`src/drafter/data/correlation.py`: causation_id, route, request_id, response_id, dom_id, phase)
directly. Concrete record types live under `src/drafter/data/details/`: `RequestEvent`,
`RequestParseEvent`, `ResponseEvent` (including `duration_ms`), `RouteAddedEvent`,
`UpdatedStateEvent`, `UpdatedConfigurationEvent`, test events, etc. `ErrorRecord` wraps an
`ErrorDetails`. The TypeScript debug panel mirrors these types in `js/src/debug/telemetry*`.

The audit helpers (`src/drafter/monitor/audit.py` - a module of functions, not a class) publish
records to the main event bus consistently: `log_error(envelope, source, ...)` for `ErrorDetails`
and `log_record(record, source, ...)` for any `TelemetryRecord`.

Current subscribers: a transient per-visit warning collector inside `do_visit`, and the
`ClientBridge` (attached via `do_listen_for_events`), which forwards records to the debug panel.

**[PLANNED]** A `Monitor` with pluggable visualizers (stdout printing, disk logs, analytics) was
designed and is referenced by commented-out code, but does not exist; `src/drafter/monitor/__init__.py`
is empty. The debug panel currently fills the "analytics" role.

## Debug Panel

The debug panel is implemented in TypeScript (`js/src/debug/`, assembled in `index.tsx`).

Implemented:

- Header quick links: home, reset state (`--reset`), About page (`--about`), and an edit button that
  opens a CodeMirror **source editor** ("Edit source and reload", dispatching
  `drafter-restart-student-code`).
- Log panel: errors/warnings/info from telemetry, nicely formatted.
- State panel: a rich typed dump of the current state (primitives, collections, dataclasses, grids,
  images, cycles).
- Routes panel: all available routes as a flat list (system routes in a collapsible section).
- History panel: page load history with request/response dumps (url, action, status, formatted
  content), pagination, per-request "Revisit", and Clear History. Response timestamps are
  client wall-clock times.
- Test panel: displays received test results (total/passed/failed, per-test pass/fail with
  side-by-side diffs on failure).
- Config panel: a live configuration override editor persisted to localStorage (see Configuration).
- Files panel: a browser for the client and host file systems with file preview.
- Footer: current route/status and the persisted-components list (reveal/evict).
- Action buttons: Home, Exit Debug, Toggle Frame; the subtle debug-entry button on deployed sites.

**[PLANNED]** (documented intent, not yet built):

- Request/response *duration* display (per-response `duration_ms` exists in telemetry but is not
  surfaced as "time taken").
- State save/load to localStorage and download/upload as JSON - header buttons exist in the markup
  but are not wired up; there is no upload button.
- Routes displayed as a graph (in addition to the flat list).
- VCR playback controls over the page-load history, and automatically produced tests from history.
- An interactive menu for building up good tests, plus a deliberately inconvenient "download
  regression tests" button (a "once your site is done" activity - we want students to think
  critically about tests rather than spamming them out).
- A REPL (the CodeMirror instance currently edits source; a REPL mode is separate).
- Test production and compile-site buttons.

## Configuration

### Structure

`SystemConfiguration` (`src/drafter/config/system.py`) is a dataclass aggregating five sub-configs:

- `BootstrapConfiguration` (`config/bootstrap.py`) - how we were launched: mode, script path, user
  directory, config-file location.
- `ClientServerConfiguration` (`config/client_server.py`) - the site's behavior/appearance; the
  config that "is" the running site.
- `AppServerConfiguration` (`config/app_server.py`) - dev-server settings (port, ws_url,
  serve_adjacent_files, ...).
- `AppBuilderConfiguration` (`config/app_builder.py`) - static-build settings (output directory,
  `pyodide_package_style` = build/cdn/pypi, additional_paths, ...).
- `AppCommonConfiguration` (`config/app_common.py`) - settings shared by server and builder:
  `engine` (pyodide/skulpt), `pyodide_url`, `system_packages`, `prerender_initial_page`,
  `mount_drafter_locally`, asset directory, etc.

All extend `BaseConfiguration` (`config/base.py`), which provides the generic machinery:
`parse_env_variables` (via the `EnvVars` helper), `parse_args`, `load_from_file`, `merge_in_args`,
`map_from_raw`, `to_json`/`from_json`, and `copy`. The singleton instance is the module-global
`_SYSTEM` in `src/drafter/configuration.py`, built by `configure_system()` and accessed everywhere
via `get_system_configuration()`.

### Phases

1. Bootstrap Phase: `BootstrapConfiguration` (its `mode` picks `start_server` vs `compile_site`).
2. Pre-initialization Phase: static `ClientServerConfiguration`.
3. Launch Phase:
   1. `AppServerConfiguration` or `AppBuilderConfiguration` (parser selected by mode).
   2. `start_server(...)` kwargs merged into the static configuration.
   3. The True Page contents are created as needed.
   4. The tracked configuration deltas are embedded in the True Page as
      `window.DRAFTER_MODIFIED_CONFIGURATION` (from `get_system_config_modifications()` /
      `_MODIFIED_ARGS`), so the client-side run reproduces the launch-time configuration.
4. Initialization Phase: static `ClientServerConfiguration` (client side, including the embedded
   modifications).
5. Configuring Phase: dynamic `ClientServerConfiguration`.

### Sources and Precedence

Static configs (lowest to highest precedence):

1. Defaults defined in the code.
2. Environment variables.
3. Command line arguments.
4. A configuration file (located via the `DRAFTER_CONFIG_FILE` env var or `--config-file`).
5. The embedded `DRAFTER_MODIFIED_CONFIGURATION` provided to the True Page via the template context
   (the determined configuration at the time of launch).

Dynamic configs (override static):

1. Imperative configuration functions in the code - `set_website_title()`,
   `set_website_framed()`, `set_website_style()`, `set_website_theme()`, `set_site_information()`,
   `hide_debug_information()`/`show_debug_information()` (`src/drafter/deploy.py`), all of which
   route through `ClientServer.reconfigure`.
2. Browser-side debug overrides: the Config debug panel persists overrides to localStorage
   (`drafter.debug.configuration-overrides.v1`, merged into the `client_server` sub-config by
   `js/src/config_overrides.ts`), layered on top of the embedded configuration.

Note that `start_server(...)` keyword arguments are merged into the **static** configuration during
the Launch Phase (before the server starts), not applied as dynamic reconfiguration.

### Default vs. Current Configuration

At runtime there are two configuration sources:

- The **default** configuration: `get_system_configuration().client_server`, exposed via
  `ClientServer.get_default_configuration()`. (The ClientServer does not itself store a
  `configuration` field.)
- The **current** configuration: stored privately on the `Site` (`Site._configuration`), exposed via
  `Site.get_configuration()` / `ClientServer.get_current_configuration()` (both return copies).

The timeline:

1. When Drafter boots, the merged static configuration becomes the default; the current
   configuration is `None`.
2. Configs applied before the server starts modify the default configuration.
3. During the **Configuring** phase (`do_configuration` → `process_dynamic_configuration`), the
   default configuration is copied to become the current configuration and stored in the `Site`.
   That copy is what actually renders the page and controls site behavior.
4. While running, dynamic reconfiguration modifies the current configuration. `reconfigure` accepts
   `update_default=True` to also update the default at the same time. Related API:
   `reconfigure_flip` (toggle a boolean), `get_config_setting`, `update_multiple_configuration`
   (with special handling for `SITE_INFORMATION_KEYS` and append semantics for the
   `additional_*_content` lists).
5. `reset` currently *clears* the current configuration (`Site.reset()` sets it to `None`); whether
   it should instead copy the default back into the current configuration is an open TODO in
   `ClientServer.reset`.

`ClientServerConfiguration` is isomorphic between default and current - its `copy()` deep-copies
every field so the two can be copied back and forth safely.

Do not mutate configuration objects directly - simply modifying fields will NOT trigger changes in
the deployed site. Call `ClientServer.reconfigure(...)`, which emits an `UpdatedConfigurationEvent`
on the event bus. The `ClientBridge` subscribes and currently reacts to changes of `framed`,
`in_debug_mode`, `enable_subtle_debug_entry`, `favicon`, `page_transition`, and
`page_transition_duration`; other keys are logged as unhandled. The page title and favicon are also
applied imperatively during site setup. **[PLANNED]**: reacting to more configuration keys
(e.g., live title updates).

The favicon pipeline: the index template always renders a `<link rel="icon" id="drafter-favicon--">`
whose href is `app_common.favicon` when set (CLI `--favicon` / `DRAFTER_FAVICON`), otherwise the
built-in Drafter icon (`scaffolding/favicon.svg`, inlined as a data URI). The user-facing
`set_website_favicon()` (or `start_server(favicon=...)`) goes through `client_server.favicon`
instead, which the bridge applies to the document at site setup and on reconfigure. The static
builder copies a favicon that references a local file into the build output.

## ClientBridge Architecture

The bridge is split into six distinct pieces (`src/drafter/bridge/`):

- `ClientBridge` (`client_bridge.py`): orchestrates startup, response handling, debug panel updates,
  and configuration-driven UI toggles.
- `SiteRenderer` (`site_renderer.py`): owns DOM setup and updates, including body/fragment
  replacement, before/after channel content, and frame toggling.
- `NavigationController` (`navigation.py`): owns request creation, browser history integration,
  initial-load navigation, and redirect loop protection.
- `EventManager` (`events.py`): owns click/submit/custom event wiring, data collection for events
  (including promise-based multi-file uploads), and hotkey registration.
- `RuntimeAdapter` (`runtime.py`): encapsulates runtime-specific behavior (Skulpt/Pyodide interop,
  event wrapping, form/file handling).
- `BrowserHistory` (`history.py`): tracks requests through pushState/popstate.

Supporting modules: `bridger.py` (the `run_client_bridge` entry function), `context.py`
(`DomContext` - per-instance window/document so multiple embedded instances don't collide),
`dom.py` (low-level DOM helpers, including shadow-DOM variants), `persistence.py` (component
parking, see above), `error_handling.py` (structured bridge error/warning reporting), `log.py`
(debug/console logging), and `client_stub.py` (a type-checker stub replaced by
`js/src/bridge/client.ts` in the built bundles).

## Multi-Instance Embedding and Shadow DOM

Multiple independent Drafter apps can run on one page (used for live examples in documentation).
`configure_instance` / `register_server` / `instance_root` in `client_server/commands.py` maintain a
registry of servers, each with its own event bus and `DomContext` (window/document pair). The site
can render into a shadow DOM (`SITE_HTML_SHADOW_DOM_TEMPLATE`, `drafter-shadow-host--`,
`use_shadow_dom`) so styles don't leak between instances or into the host page.

## File System

A key element of Drafter applications is file access. The Host (CPython) has a real disk file
system; the Client (browser runtime) needs a virtual one.

### What is implemented

- **Custom `open`** (`src/drafter/files/opening.py`): exported via `from drafter import *` and also
  installed as `builtins.open`.
  - Host side: relative paths are resolved against the student's main-script directory
    (`bootstrap.get_user_directory()`, falling back to the current working directory); URLs can be
    opened directly (fetched into StringIO/BytesIO).
  - Pyodide side: resolve the instance path → try the Emscripten virtual FS → on FileNotFoundError,
    fetch the original path from the server via XMLHttpRequest (200 → in-memory file; otherwise
    FileNotFoundError). Writes go to the virtual FS.
  - Skulpt side: reads resolve through `Sk.builtinFiles` only (`js/src/skulpt_bridge/ skulpt-tools.ts`), seeded at precompile time. There is no fetch fallback on the Skulpt path.
- **Imports**:
  - Host-side execution uses Python's normal import machinery.
  - Pyodide: a `RemoteFinder` MetaPathFinder (`src/drafter/files/patch_pyodide.py`) fetches student
    `.py` modules from the server on demand (with `expire_remote_imports` for hot-reload cache
    invalidation). The Drafter library itself is provided either as a built `drafter-pyodide.zip`,
    from PyPI via micropip, or from a CDN, depending on `pyodide_package_style`.
  - Skulpt: imports resolve through the same `builtinFiles` read function (no separate import
    hook).
- **Serving adjacent files**: the dev server (when `serve_adjacent_files` is true, the default)
  mounts the student's directory as static files at `/` (with a path-traversal guard) and exposes a
  JSON listing endpoint (`__drafter_list_files`). The static build copies assets and configured
  `additional_paths` globs into the output directory, so relative URLs work identically when
  deployed. Images are assumed to be available via the server.
- **Error logging**: outside production mode, the debug panel batches error envelopes to the dev
  server's `__drafter_error_log` endpoint (`js/src/debug/error_reporter.ts`, disabled for the
  session after the first failed delivery). The server appends them, plus bug-report-style
  environment details, to a shared JSON Lines file `drafter-debug.log` next to the student's code
  (`src/drafter/app/error_log.py`, size-capped with best-effort trimming); the file watcher ignores
  that file so log writes never trigger reloads.
- **Uploads**: uploaded files are read into memory (`RuntimeAdapter.handle_file_upload`) as
  `{filename, content, type, size}` dicts and injected into the request data.
- **Native directory mounting**: Pyodide can mount a real local directory via `mountNativeFS`, with
  the directory handle persisted in IndexedDB (`js/src/pyodide_bridge/directories.ts`).
- **Debug access**: the Files debug panel browses both the client virtual FS and the host FS.

Module layout note: the live code is the `src/drafter/files/` **package** (`opening.py`,
`patch_pyodide.py`). `files/file_system.py` is an empty placeholder for a future unified interface.
The sibling `src/drafter/files.py` module is orphaned v1 template code (shadowed by the package)
and should be deleted along with `command_line.py`.

### [PLANNED] file-system work

- A unified client file-system interface spanning: in-memory, localStorage, IndexedDB, the
  read-only server assets, and a writeable server backend (e.g., database-style writing through
  Firebase). Today only the in-memory/virtual FS and the read-only server fetch exist;
  localStorage/IndexedDB are not file-system backends, and there is no writeable-server or Firebase
  integration.
- Write-mode fallbacks (localStorage first, then ask the server, erroring unless the server
  supports writes).
- A compile-time **manifest** of all available files (with an ignore-list concept) provided to the
  client file system, instead of ad-hoc copying. (The closest existing thing is the
  `skip_extensions` filter when building the pyodide zip.)
- Absolute-path policy: by default tell the student "stop using absolute paths that won't work,"
  with a command-line flag to allow them (TODOs exist in `opening.py`); explicit configuration for
  resolving relative paths against cwd vs. the main script.
- Associating uploaded files with state and restoring them on back/forward navigation, with a
  strategy for large files (IndexedDB, prompting re-upload, or substitution).
- `requirements.txt` handling and automatic import detection across all student files.
- Deciding who owns file-system access (bridge, debug panel, student code via wrapped `open`,
  ClientServer for logs, builder for output, app server for serving) behind one interface that can
  make decisions on the fly from configuration - including during student code execution, not just
  at launch.

## Serving, Building, and Packaging

Here are the parts of Drafter that have to be hosted:

- **Drafter Python library**: the core library for CPython, published on PyPI as `drafter` (built
  with hatchling; see `pyproject.toml`).
- **JS/CSS assets** (built by tsup from `js/` into `js/dist/`):
  - `drafter.skulpt.js` - the bundle integrating Drafter with the Skulpt environment.
  - `drafter.pyodide.js` - the bundle integrating Drafter with the Pyodide environment.
  - (There is no unified `drafter.js`; the two engine bundles are the entry points.)
  - `drafter_base.css` - core styling.
  - `drafter_debug.css` - debug menu styles.
  - `drafter_deploy.css` - styles for deployed (non-debug) mode.
  - Themes (registered in `src/drafter/styling/themes.py`): `default`, `none` (special-cased to no
    stylesheets), `almond`, `brutal`, `darkfairy`, `daub`, `latex`, `magick`, `matcha`, `mvp`,
    `pico`, `retro`, `sakura`, `simple`, `skeleton`, `tacit`, `terminal`, `water`, `yorha`, and the
    retro Windows themes `98`, `xp`, and `7`. The student docs catalog deliberately omits
    `darkfairy` and `matcha` (registered but dormant).
- **Skulpt libraries** (built into `js/dist/skulpt/` by helper scripts, not part of the default
  build): `skulpt.js` and `skulpt-stdlib.js` (fetched/copied by `npm run update-skulpt`), and
  `skulpt-drafter.js` (the Skulpt-precompiled Drafter Python, produced by `npm run precompile`,
  which already includes `--minify`).
- **Pyodide**: not vendored. Pyodide core is loaded from a CDN by default
  (`DEFAULT_PYODIDE_URL` base + `pyodide_version` + `pyodide_branch`, composed by
  `AppCommonConfiguration.get_pyodide_url()`; overridable via `--pyodide-url`,
  `--pyodide-version`, `--pyodide-branch` or the matching `DRAFTER_PYODIDE_*` env vars), and
  the Pyodide-compiled Drafter ships as `drafter-pyodide.zip`, via PyPI/micropip, or via CDN
  depending on `pyodide_package_style`.
- **Precompiled headers/body**: the pre-rendered initial page content (see The First Page). These
  are generated at serve/build time by `precompile_server`, not shipped as static build artifacts.
- **Student assets**: images, additional Python files, CSS, etc., copied/served as described in
  File System.

### Asset flow

Built assets are **not** vendored into the Python source tree. The flow is:

- `js/dist/` is the single build output (`npm run build` → `dist/js` + `dist/css`).
- At Python package build time, hatchling force-includes `js/dist/` into the wheel as
  `drafter/assets/` (`pyproject.toml`).
- At runtime, `pkg_assets_dir()` (`src/drafter/scaffolding/utils.py`) returns the installed
  `drafter/assets/` directory if it exists (installed-wheel case) or falls back to the repo's
  `js/dist/` (source-checkout/dev case). The dev server mounts it as static files; the builder
  copies it into the output directory.
- The old `js/scripts/sync-dist.mjs` (which copied dist into the source tree) is deprecated and
  unused; `js/scripts/resolve-assets.mjs` is likewise orphaned.

Serving comes in two flavors:

- **Developer**: working locally on Drafter itself, you get the locally compiled `js/dist` assets
  automatically via the fallback above (`mount_drafter_locally` also exists as a flag).
- **Student**: students get the assets bundled in the installed wheel. **[PLANNED]**: an official
  hosted/CDN location for Drafter's own JS/CSS so static builds can link out instead of copying;
  currently only Pyodide core and some third-party CSS come from CDNs. (The old Skulpt CDN
  parameters from v1 are still parsed but explicitly ignored with a warning.)

### CI/CD

Current workflows (`.github/workflows/`):

- `test_and_lint.yml`: builds the JS (`npm ci` + `npm run build`, uploading `js/dist` as an
  artifact), runs jest (non-blocking), lints (ruff + mypy), runs the Python test matrix
  (3.10–3.14), and builds the package (`uv build`), verifying the wheel contains the bundled
  assets.
- `docs.yml`: builds the JS and the MkDocs site and deploys to GitHub Pages on pushes to main.

The Justfile mirrors the local versions of these steps (`just build` = build JS then `uv build`).
Note that the Skulpt steps (`update-skulpt`, `precompile`) are currently *not* wired into CI or the
Justfile - only the tsup build runs.

**[PLANNED]** publishing automation: on merging a release to main, a workflow should publish to
PyPI (`drafter`) and NPM (the `js/` package is `drafter-js-client`, marked publishable but never
yet published by CI). A separate WebAssembly-targeted PyPI distribution has been discussed but is
not configured. For Skulpt publishing, the build system will need a stable Skulpt version
available.

## Known Legacy / Cleanup Targets

- `src/drafter/command_line.py`: orphaned v1 CLI/builder (self-described as deprecated); nothing
  imports it via the active entry points.
- `src/drafter/files.py`: orphaned v1 template constants, shadowed by the `files/` package.
- `src/drafter/hacks.py`, `src/drafter/app/hacks.py`: transitional patches.
- The unused `JSON_DECODE_SYMBOL` constant (superseded by `data-transform="json-decode"`).
- `js/scripts/sync-dist.mjs` and `js/scripts/resolve-assets.mjs` (superseded by the hatchling
  force-include + `pkg_assets_dir()` fallback).
- Commented-out `Monitor` wiring in `client_server.py` (pending the Monitor design in Telemetry).

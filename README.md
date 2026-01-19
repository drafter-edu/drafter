# Websites

A simple Python library for making websites

git checkout v2-pyodide

## Development

### Setup (Python via uv)

1. **Prereqs**: Python 3.8+ (recommended 3.11+), Node.js 18+ with npm, and [uv](https://github.com/astral-sh/uv). On Windows PowerShell:

```powershell
winget install astral-sh.uv
```

2. **Clone**:

```powershell
git clone https://github.com/drafter-edu/drafter.git
cd drafter
```

3. **Create the Python environment and install deps** (reads pyproject/uv.lock):

```powershell
uv sync
```

4. **Install JS deps once** (for builds/watchers):

```powershell
cd js
npm install
cd ..
```

5. **Run an example** (uses uv’s virtual env automatically):

```powershell
uv run examples\shop.py
```

If you need the Skulpt engine explicitly, pass `--engine skulpt`.

### watch JS assets

To iterate on the JS client and have changes flow into the Python package automatically:

1. In one terminal, run the JS watcher. This rebuilds the TypeScript bridge on every save and copies the output into `src/drafter/assets`:

```powershell
cd js
npm install
npm run dev
```

2. In another terminal, run the JS precompiler. This builds the Skulpt version of the Python Drafter library on every save and copies the output into `src/drafter/assets`:

````powershell
cd js
npm run precompile:watch
```

3. In another terminal, run a local Drafter app so you can see live reloads. For example, using one of the examples:

```powershell
uv run examples\simplest.py
````

Notes:

- The watcher writes bundles to `src/drafter/assets` which the dev server serves from `/assets` and is already included in the server's file-watcher, so connected browsers will auto-reload.
- If you maintain a local Skulpt build, set `SKULPT_DIR` in a top-level `.env` to copy `skulpt.js` and `skulpt-stdlib.js` directly into `src/drafter/assets` on startup (`npm run dev` calls this automatically).

### run tests

- JS tests:

```powershell
cd js
npm run test
```

- Python tests (uses uv env):

```powershell
uv run pytest --verbose --color=yes -vv
```

## Organization

When you run a Drafter program that has a `start_server` call, then it will actually trigger the `launch.py` script's logic that will either run the application differently depending on whether it is in Skulpt/Pyodide (web) mode or normal Python (app) mode.

If a user runs the program directly, then when it reaches `start_server`, it will start a local development server (the `AppServer`) using Starlette.
This server will serve a single page with a div that contains the DRAFTER_ROOT.
The page will sets up Skulpt/Pyodide and a hot-reload connection to the server.
Finally, the page will also load the user's code into Skulpt/Pyodide and run it, which should rerun this process from the beginning, but instead triggering the alternative path where we run in `web` mode (see below). Effectively, this is running the program twice. The first time is "server side" with no real implications (other than starting the server, unit tests, print statements, etc.). The second time is "client side" in Skulpt/Pyodide, where the user's code is actually run.

If the `build` command is used from the command line script, then the `AppBuilder` will instead generate static HTML, CSS, and JS files that can be deployed to any static hosting service.
The main `index.html` file will create the DRAFTER_ROOT div, set up Skulpt/Pyodide and load the user's code into it.
It will try to render the student's initial page to prepopulate as much meta information as it can, as well as an HTML preview that can be shown for SEO contexts.
The `AppBuilder` and `AppServer` are together both referred to as `AppBackend`.

If the user is running the program directly in Skulpt/Pyodide, then when it reaches the `start_server` call, it will instead trigger the `launch.py` script's logic to setup the `ClientBridge`, `Client`, and get the main `ClientServer`. Note that the `ClientServer` is not a real server; it is just a class that handles requests from the `Client` and generates responses.
The `ClientBridge` is responsible for populating the DOM, tracking user interactions, and sending requests from the client side, while the `ClientServer` is responsible for processing requests, managing state, and generating responses on the server side.

The area that the user sees is the `Site`, which is a frame encapsulating the `Form`, the `Body` (composed of `PageContent`), the `DebugInfo`, and additional elements that are needed (e.g., audio players).
The `Site` is a container that holds all the elements of the user interface and is populated by the `ClientBridge` based on the responses it gets from the `ClientServer`.
The `ClientBridge` is stupid when it comes to the site, and doesn't really understand what it has; as much of that logic as possible is pushed into the `ClientServer`.
The `ClientServer` generally sends information to the `ClientBridge`, which then performs updates on the page (e.g., sending info to the `DebugInfo` panel, updating the `PageContent`, adding new JS/CSS, etc.).

The DOM structure of the site is as follows:

- There's a top-level div tag with id `drafter-root--` that contains ALL content (except for top-level script tags needed for loading the actual true initial page).
- There's a div tag with id `drafter-site--` that contains the entire site.
- Inside that is a `drafter-frame--` div that contains the main app, followed by the `drafter-debug-info--` div.
    - The frame makes the app look like it is in a browser window.
    - The frame is only visible in development mode; otherwise, only its content is visible.
- Inside the frame is a `drafter-header--` div, a `drafter-body--` div, and a `drafter-footer--` div.
    - The header and footer are only visible in development mode.
    - The header has things like the site title and quick links for resetting state, going to the about page, etc.
    - The footer has quick information like the current route, status, etc.
- The first child of the `drafter-body--` is a `form` tag with id `drafter-form--`.
- Subsequent children of the body can be additional tags that are outside the form (e.g., modals, audio players, etc.).
- When the page content is rendered, it replaces content within the header/body/footer that is inside of the Form (without replacing the form itself).

The structure can be summarized as:

- Root > Site > Form > Frame > Header
- Root > Site > Form > Frame > Body > (Page's content goes here)
- Root > Site > Form > Frame > Footer
- Root > Site > DebugInfo

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

We'll use a request/response model to update the page content, based around events.
When the user interacts with the page (clicks a link, submits a form, etc.), the `ClientBridge` will send a request to the `ClientServer` with the relevant information:

- The action that led to the request (e.g., "click", "back", "forward", "reset button")
- The URL path being requested (which will match to a route function)
- The form data (which will be unpacked into named parameters, if matched)
    - Input forms
    - Files
    - The `Argument` objects
- Extra event information, passed as its own dataclass instance in a specially named `event` parameter.
    - Clicked button
    - Scroll position
    - Etc.

The `ClientServer` will process the request and choose an appropriate route handler by using the `visit` method.
The provided function will be called, providing the current State and the request information (via named parameters).
That function is expected to return a `ResponsePayload`, which can be any of various subclasses: `Page` (the most common), `Fragment`, `Update`, `Redirect`, `Download`, `Progress`, `ErrorPage`. That Page gets post-processed and wrapped in a `Response` along with metadata (e.g., status code, errors, headers, etc.) and sent to the `ClientBridge`. The `Response` is always sent back to the `ClientBridge`, even in error cases. Think of the Payload as being "the thing we will show the user", while the Response is "the meta information for the system." So most error metadata will be in the Response, while the Payload might still be a Page that shows a friendly error message.

Note that route functions usually expect `state: State` as their first parameter, but you can also do `page: Page` instead if you want to get the current state of the Page object (which includes the State). The `ClientServer` will automatically provide the appropriate object based on the function signature. So the complete list of "special" route parameter names:

- `state: Any`: The current State object; only if this is the first parameter.
- `page: Page`: The current Page object (which includes the State); only if this is the first parameter.
- `event: Event`: The event information as a dataclass instance.
- `kwargs: dict`: Any other form fields that were not matched to named parameters will be provided as a dictionary in this parameter.
- `request: Request`: The full raw Request object, if desired.

The `ClientBridge` will then unwrap the page contents and update the DOM faithfully according to whatever it got from the `Response`, changing the contents of the `form` and replacing the click handler. It should update the browser history as appropriate, and run any scripts that were included in the response. If it had any errors or warnings, it should display those in the debug panel.

A `ResponsePayload` has a few key methods that should be implemented to fit into the lifecycle:

- `verify`: Before being sent to the client, the `ResponsePayload` is verified to ensure it is valid and can be rendered properly. This might include checking for required fields, ensuring that links are valid, etc.
- `render`: The payload is rendered in the `ClientServer` by calling its `render` method, which produces HTML. Typically, for a `Page`, this involves rendering all of its components and assembling them into a complete HTML document fragment. Note that this must be done recursively, so that each component renders its children, and so on.
- `get_messages`: The payload can also generate any additional scripts that need to be run before or after the main content is inserted; these are sent along as part of the `Response` and executed by the `ClientBridge`. This is all facilitated by the `channels` of the `ClientBridge` and `ClientServer`, which allow sending messages back and forth; this is also useful for things like controlling page-level audio. So a `ResponsePayload` generates its messages, and these messages are sent to the `ClientBridge` to be executed at the appropriate time.
- `format`: The payload is turned into a string that can be used to recreate the payload, essentially the same as `repr`. This is useful for debugging and logging purposes.
- `get_state_updates`: If the payload needs to make any changes to the `State` (e.g., updating fields, adding history entries, etc.), it can provide those updates via this method. The `ClientServer` will apply these updates to the current `State` after processing the request but before sending the response back to the client.

After the response is successfully (or unsuccessfully) processed, the `ClientBridge` sends notifications to the Audit system.

How is the first page handled? When the server starts up, it will create an initial State object. While Starlette or the compiler is going through its initial setup run of the code, it will find the `index` route and execute it to generate initial page content (this can be disabled if needed). This information is provided in the generated template that the server serves to the client, so that SEO crawlers can see the initial content.
When the `ClientBridge` connects, it will immediately request the index page (unless a specific other page was requested first, via query arguments), which will be run on the `ClientServer` side to generate the actual page content for the user.

How are errors and warnings handled? At any point during the process, we can generate either errors or warnings, and they get attached to the eventual `Response` AND also sent out through Telemetry. In some cases, we may want to short-circuit the normal flow and return an error response immediately (e.g., if a route handler raises an exception). In other cases, we may want to accumulate warnings and send them along with a successful response. There are many kinds of errors, all of which are documented in the `drafter.data.error` module.

How is History handled? Whenever a Request/Response completes, the Bridge notifies the `PersistentStorage` to store relevant data. That system uses the current Session ID in order to persist data that can then be restored if the page is reloaded or navigated back to. It has to keep track of everything in such a way that it can play it back later. This includes the State, the accessed pages, the arguments used, and any files that were uploaded. These updates should happen asynchronously wherever possible.

When the user navigates back or forward without leaving the site (e.g., since we hijacked the back button), the `ClientBridge` sends a request with the appropriate State ID, and the `ClientServer` retrieves that State and generates the corresponding page content. This allows for seamless navigation through the user's history of interactions with the site. When a tab gets opened, we check to see if the sessionStorage has a session ID for this tab. This can happen when the user navigates away to a different server and then comes back (e.g., via the back button). If there is no session ID, we generate a new one and store it in sessionStorage. This allows us to maintain continuity across page reloads and navigations within the same tab.

How are streaming responses handled? How are long-running tasks handled? In both cases, we can yield `Progress` payloads from route handlers, which will be sent to the `ClientBridge` as they are generated. The `ClientBridge` can then update the page to show progress indicators or partial results as they come in. This means that a single request can actually result in multiple responses being sent to the client over time.

From the student developer's perspective, they are building a `Site`, which can have multiple `Route`s. A `Route` is a decorated function that takes in the current `State` and any relevant parameters, and returns a `Page` (or other `ResponsePayload`). A `Site` also has metadata like title, description, favicon, language, etc.

- How do users create "dynamic" route functions? They don't. Instead, they should focus on parameterizing their route functions appropriately. This still allows for dynamic behavior using response payloads like `Fragment`, where you attach a route to a component that can then be triggered through some other kind of event. For example:
    - A textbox has an `on_change` event that is meant to do live validation of the text that the user is typing. The `on_change` event can be linked to a route function that takes in the current state and the text value, and returns a `Fragment` that updates the validation message below the textbox. Rough pseudocode:

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

TODO: Decision about the query selector. We could do something complicated where we try to detect what the user wants, just use regular query selectors, or have some custom functions (e.g., by_id, by_class, by_name, by_tag). Do we want to do this JQuery style where it selects all matching elements, or just the first one?

How does updating the page content work? The `Page` payload has an HTML string that is going to be injected into the page at the `drafter-body--` div. The `Fragment` payload has an HTML string that is going to be injected into a specific component on the page, identified by the query selector provided. So essentially a Page is just a Fragment with a predefined target location.

A `URL` is a string that represents a unique `Route` function in the `Site`. It should follow the naming conventions of a Python function (e.g., lowercase letters, numbers, underscores, no spaces or special characters). Eventually, we might support slashes for things like classes or modules (which would probably translate to periods).

Things that have to be kept in the server:

- State
- Initial state (for resetting)
- Accessed pages, args
- History of state
- History of request parameters, which includes files.

The debug information present in the frame:

- Quick link to reset the state and return to index
- Link to the About page
- Status information:
    - Any errors and warnings, nicely formatted
    - Current route information, as given by the `request.visit` events
    - Request/Response dump, including the metadata and actual contents, time taken.
    - Current state dump, buttons to save/load state in localStorage or download/upload JSON (`state.*` events)
    - Current page information (`request.*` events)
    - All available routes (`request.add` events)
        - As a flat list
        - As a graph
    - Page load history (`request.*` events)
        - Pages, state, args, timestamps, etc.
        - VCR playback controls
        - Automatically produced tests
    - Test status information (`request.visit` events)
        - There should be an interactive menu for building up good tests
        - An inconvenient download button for downloading "regression tests". Make this more of a "once your site is done" sort of thing, instead of encouraging them to do it all the time. I would like them to think critically about their tests instead of just spamming them out.
    - Button to activate codemirror instance that let's us do a REPL type thing?
- Test production button
- Compile site button

The `EventBus` is a pub/sub system that allows different parts of the application to communicate with each other without being tightly coupled. Various components can publish events to the bus, and other components can subscribe to those events to receive notifications when they occur (mostly the Monitor).
Telemetry entails logging events like page loads, errors, warnings, state, performance metrics, user interactions, etc. Essentially, any debug information from the server should
be logged as `TelemetryEvent`, and certain kinds of client interactions. To help figure out where the data came from, there is also `TelemetryCorrelation`. Think of the `TelemetryEvent` as the envelope around the actual event data (which are subclasses of the `BaseEvent`).
The `Monitor` has visualizers that can handle the rendering logic for different contexts: raw information to be printed on stdout, logs for storing on disk, analytics for displaying in the debug panel.
The `Audit` module has a bunch of helper functions for publishing `TelemetryEvent` to the main EventBus in a consistent manner.

Essentially:

- The `ClientBridge` handles all DOM manipulation and user interaction on the client side.
- The `ClientServer` processes requests, manages state, and generates responses on the server side
- The `Page` (and other `ResponsePayload`s) represent the content and structure of the pages being served, and are created by the user-developer.
- The `Request` wraps user interaction data for transmission from client to server, and is created by the `ClientBridge`.
- The `Response` wraps the `ResponsePayload` with metadata for transmission between client and server, and is created by the `ClientServer`.

How is `open` and `read` handled? Skulpt should first check builtinFiles, then localStorage (or IndexedDB if configured), and then ask its server using fetch. If its server (Starlette or Github Pages) can't find it, it should 404. If it's using write mode, then it should try to write to localStorage first, and then ask its server to write it (which will cause an error unless we're on a real server that supports it).

Images will assume to be available via the server.

Reentrant pages: If a route function has default parameters, then the URL can be called without those parameters, and the defaults will be used. This allows for reentrant URLs that can be bookmarked or shared.

File handling: When a file gets uploaded to the server, it will get stored in memory (or IndexedDB/localStorage if needed) and associated with the current state. When navigating back and forth, the file will be restored as needed. Note that files past a certain size may not be storable in localStorage, so we may need to have a strategy for handling large files (e.g., using IndexedDB, prompting the user to re-upload, substituting a smaller file).

`PersistentStore` is a class that lives in the ClientBridge which abstracts away the details of where data is stored (in-memory, localStorage, IndexedDB, etc.). It provides a simple interface for saving and loading data, and can be configured to use different storage backends as needed. The server can send commands to the ClientBridge to store or retrieve data using this `PersistentStore`.

### Summary of Execution Timeline

1.  User runs a Drafter program that has a `start_server` call.
2.  The `launch.py` script compiles a simple HTML version of the initial page for pre-rendering
3.  The `launch.py` script starts up the Starlette server
4.  The initial True Page gets served to the browser
5.  The True Page sets up the WebSocket connection back to the App Server
6.  The True Page sets up the Skulpt/Pyodide environment
7.  The True Page executes the student's code
8.  Drafter is imported; the `MAIN_SERVER` (`ClientServer`) and `MAIN_EVENT_BUS` (`EventBus`)are created.
9.  The rest of the students' code is executed, adding routes to the `MAIN_SERVER` as it goes, until it reaches the `start_server` call.
10. The `launch.py` script creates the `ClientBridge`
11. The `ClientServer` is configured, processing its static and dynamic configuration (see below).
12. The Site is (re-)rendered:
    1.  The `ClientServer` creates the True page structure
    2.  The `ClientBridge` loads the rendered site with interactivity
    3.  The `ClientBridge` sets up the Debug Menu.
13. The `ClientBridge` starts listening to the `ClientServer`'s event bus to handle telemetry
14. The `ClientServer` is started
    1.  The state is updated based on the initial state.
    2.  The router is registered with default routes
15. The `ClientServer` starts handling events, starting with the initial route (defaults to `index`)
    1.  The `ClientServer` is `visit`ed with the Request, and returns a `Response`
    2.  The `ClientBridge` handles the response, updating the page content and attaching the new handlers.
16. The `ClientBridge` sets up page-wide navigation handlers (e.g., `popstate`, `drafter-navigate`)
17. The `ClientBridge` sets up a hotkey binding for the Debug Menu to be toggled on/off.
    1.  If clicked, then the site is re-rendered (see above) and the initial route is re-visited.

At that point in time, the site is considered launched. Now, whenever a navigation event occurs (e.g., via a click), the following happens:

2. The `Client` prepare a new `Request` object with the relevant information (e.g., route, args, event data)
3. The `Client` sends the `Request` to the `ClientServer` via the connection established by the `ClientBridge` (a "Visit")
    1. The `ClientServer` gets the route function based on the request
    2. The `ClientServer` executes the route function and generates a a `Payload`
        1. The `ClientServer` delegates argument preparation to its `Router`
        2. Then the `ClientServer` safely executes the route function, catching any exceptions and converting them into `ErrorPage` payloads as needed.
    3. The `ClientServer` verifies the `Payload`
    4. The `ClientServer` renders the `Payload` to generate the new HTML body
    5. The `ClientSerer` formats the `Payload` to generate a string representation for logging/debugging purposes
    6. The `ClientServer` updates its state based on the `Payload`
    7. The `ClientServer` generates any messages that need to be sent to the `ClientBridge`
    8. The `ClientServer` returns a successful response with the information above.
4. The `ClientBridge` receives the `Response` from the `ClientServer`, and handles it:
    1. The `ClientBridge` removes all the page-specific content currently in place.
    2. The `ClientBridge` injects "Before" channel content (e.g., styles, scripts) that came with the `Response`.
    3. The `ClientBridge` asks the `Client` to update the page
        1. The `Client` notifies te debug panel of the new route
        2. The `Client` updates the body content if any is given
        3. The `Client` mounts the navigation handlers
    4. The `ClientBridge` injects "After" channel content (e.g., styles, scripts) that came with the `Response`.
    5. If it was a redirect route, then we handle the redirect now.
        1. We first check to make sure we are not in a loop
        2. We make a new request from the response
        3. We send the request, and start over from the top, as we did before.

A complicated substep is the argument preparation:

1. The `Router` makes a fresh version of the arguments
2. The `Router` preprocesses the buttons, which are labeled in a special way.
    1. TODO: Check if this is actually still necessary?
3. The `Router` inspects the signature of the route function
4. The `Router` converts hidden form parameters
5. The `Router` flattens any keyword arguments that are lists
6. The `Router` injects the current state into the arguments if there is a `state` parameter
7. The `Router` removes excess arguments
8. The `Router` converts arguments to their destination types
9. The `Router` verifies that all expected parameters are present
10. The `Router` builds a string representation of the arguments for logging/debugging purposes

### Error Handling

Here's how each kind of error is handled:

- Core infrastructure during initial entire page load (e.g., Skulpt setup)
- Route resolution errors (e.g., no matching route, argument parsing errors)
- Errors during route execution (e.g., exceptions raised in route handlers) in student code

Here are the places that we can show errors to the user:

- The drafter page content area, where we can show friendly error messages that are styled to fit the site. This is the most common place for errors to be shown, and is where we would show things like "404: Page not found" or "500: Internal server error", as well as any custom error pages that the user might create.
- The entire page, if Drafter's infrastructure fails to load at all.
- The debug panel, where we can show error events.
- The browser console, where we can log errors for debugging purposes. This is generally for error details that are more serious and might indicate a bug in the framework itself, rather than just an error in the user's code.
- An `alert` popup, which can be used for critical errors that require immediate attention. This should be used sparingly, as it can be disruptive to the user experience.

### Configuration

The configuration settings can come from a few different places; here they are in order of precedence (dynamic will override static, and highest will override lower):

- "Static" configs:
    1.  Defaults defined in the code
    2.  Environment variables
    3.  Command line arguments
    4.  A configuration file (provided by either 1. the environment variables, or 2. command line arguments)
- "Dynamic" configs:
    1.  Imperative configuration functions in the code (e.g., `set_site_title()`)
    2.  Arguments passed to the `start_server` function

At runtime, there are two main sources of configuration information:

- The "current" configuration, which is stored in the `Site`
- The "default" configuration, which is stored in the `ClientServer`'s `configuration` field.

Here's the configuration timeline:

1. When the Drafter module first boots up, its static configuration is determined by merging those config sources together. This becomes the **default configuration** and is stored in the `ClientServer`'s `configuration` field. The **current configuration** will be `None` for now.
2. Further dynamic configs before the server starts will modify the default configuration.
3. When the `ClientServer` is rendered, the default configuration is copied to become the **current configuration** and stored in the `Site`, which is what is actually used to render the page and control the behavior of the site.
4. While the `ClientServer` is running, any dynamic configs will modify the current configuration. A boolean keyword parameter `update_default` can be provided to also update the default configuration at the same time if desired.
5. The user can `reset` the site, which will copy the default configuration back to the current configuration, resetting dynamic changes made AFTER the server started.

The `ClientServerConfiguration` dataclass is meant to be isomorphic between the **default** and **current** configurations, so that they can be easily copied back and forth.

Separate from this are the interfaces for the various configuration systems, which must map to the `ClientServerConfiguration` in order to actually affect the behavior of the system. For example, environment variables and command line arguments might be very different from the arguments provided to the `start_server` function, but they all need to be translated into the appropriate fields in the `ClientServerConfiguration` dataclass.

The `server.default_configuration` and `server.site.configuration` are not meant to be accessed directly.
In particular, this is because simply modifying their fields' contents will NOT trigger changes in the
deployed site.
You have to call the `reconfigure` method on the `ClientServer` in order to actually trigger any changes.
Interested parts of the `ClientBridge` can subscribe to configuration change events on the `EventBus` in order to know when to update things like the page title, favicon, etc. whenever the configuration changes.

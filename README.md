# Websites

A simple Python library for making websites

## Organization

When you run a Drafter program that has a `start_server` call, then it will actually trigger the `launch.py` script's logic that will either run the application differently depending on whether it is in Skulpt (skulpt) mode or normal Python (app) mode.

If a user runs the program directly, then when it reaches `start_server`, it will start a local development server (the `AppServer`) using Starlette.
This server will serve a single page with a div that contains the DRAFTER_ROOT.
The page will sets up Skulpt and a hot-reload connection to the server.
That page will also load the Drafter library in Skulpt, which includes a specialized version of the client library (which adds new functionality to `ClientBridge`).
Finally, the page will also load the user's code into Skulpt and run it, which should rerun this process from the beginning, but instead triggering the alternative path where we run in Skulpt mode (see below). Effectively, this is running the program twice. The first time is "server side" with no real implications (other than starting the server, unit tests, print statements, etc.). The second time is "client side" in Skulpt, where the user's code is actually run.

If the `build` command is used from the command line script, then the `AppBuilder` will instead generate static HTML, CSS, and JS files that can be deployed to any static hosting service.
The main `index.html` file will create the DRAFTER_ROOT div, set up Skulpt and load the user's code into it, as well as load the Skulpt version of the Drafter client library to set up the page content.
It will try to render the student's initial page to prepopulate as much meta information as it can, as well as an HTML preview that can be shown for SEO contexts.
The `AppBuilder` and `AppServer` are together both referred to as `AppBackend`.

If the user is running the program directly in Skulpt, then when it reaches the `start_server` call, it will instead trigger the `launch.py` script's logic to setup the `ClientBridge` and get the main `ClientServer`. Note that the `ClientServer` is not a real server; it is just a class that handles requests from the `BridgeClient` and generates responses.
The `BridgeClient` is responsible for populating the DOM, tracking user interactions, and sending requests from the client side, while the `ClientServer` is responsible for processing requests, managing state, and generating responses on the server side.

The area that the user sees is the `Site`, which is a frame encapsulating the `Form`, the `PageContent`, the `DebugInfo`, and additional elements that are needed (e.g., audio players).
The `Site` is a container that holds all the elements of the user interface and is populated by the `BridgeClient` based on the responses it gets from the `ClientServer`.
The `BridgeClient` is stupid when it comes to the site, and doesn't really understand what it has; as much of that logic as possible is pushed into the `ClientServer`.
Different parts of the `Site` are updated from different parts of the `ClientServer`: the `Monitor` has control over the `DebugInfo`, while the `Route` handlers have control over the `PageContent`.

The DOM structure of the site is as follows:

-   There's a top-level div tag with id `drafter-root--` that contains the entire site.
-   There's a div tag with id `drafter-site--` that contains the entire site.
-   Inside that is a `drafter-frame--` div that contains the main app, followed by the `drafter-debug-info--` div.
    -   The frame makes the app look like it is in a browser window.
    -   The frame is only visible in development mode; otherwise, only its content is visible.
-   Inside the frame is a `drafter-header--` div, a `drafter-body--` div, and a `drafter-footer--` div.
    -   The header and footer are only visible in development mode.
    -   The header has things like the site title and quick links for resetting state, going to the about page, etc.
    -   The footer has quick information like the current route, status, etc.
-   The first child of the `drafter-body--` is a `form` tag with id `drafter-form--`.
-   Subsequent children of the body can be additional tags that are outside the form (e.g., modals, audio players, etc.).
-   When the page content is rendered, it goes inside the `form` tag.

The structure can be summarized as:

-   Root > Site > Frame > Header
-   Root > Site > Frame > Body > Form > (Page's content goes here)
-   Root > Site > Frame > Footer
-   Root > Site > DebugInfo

We'll use a request/response model to update the page content, based around events.
When the user interacts with the page (clicks a link, submits a form, etc.), the `BridgeClient` will send a request to the `ClientServer` with the relevant information:

-   The URL path being requested
-   The form data
    -   Inputs
    -   Files
    -   Args
-   Extra event information
    -   Clicked button
    -   Scroll position
    -   Etc.

The `ClientServer` will process the request and choose an appropriate route handler by using the `visit` method.
The provided function will be called, providing the current State and the request information (via named parameters).
That function is expected to return a `Page` (or eventually other valid response payload types: `Fragment`, `Update`, `Redirect`, `Download`, `Progress`). That Page gets post-processed and wrapped in a `Response` along with metadata (e.g., status code, errors, headers, etc.) and sent to the `BridgeClient`.

The `BridgeClient` will then unwrap the page contents and update the DOM faithfully according to whatever it got from the `Response`, changing the contents of the `form` and replacing the click handler. It should update the browser history as appropriate, and run any scripts that were included in the response.

The `Page` is rendered in the `ClientServer` by calling its `render` method, which produces HTML. It also generates any additional scripts that need to be run before or after the main content is inserted; these are sent along as part of the `Response` and executed by the `BridgeClient`.
This is all facilitated by the `channels` of the `BridgeClient` and `ClientServer`, which allow sending messages back and forth; this is also useful for things like controlling page-level audio.

After the response is successfully (or unsuccessfully) processed, the `BridgeClient` sends back an `Outcome` to the `ClientServer`, indicating whether the operation succeeded or failed, along with any relevant info, warnings, or errors.

How is the first page handled? When the server starts up, it will create an initial State object. While Starlette or the compiler is going through its initial setup run of the code, it will find the `index` route and execute it to generate initial page content (this can be disabled if needed). This information is provided in the generated template that the server serves to the client, so that SEO crawlers can see the initial content.
When the `BridgeClient` connects, it will immediately request the index page, which will be run on the `ClientServer` side to generate the actual page content for the user.

How are errors and warnings handled? At any point during the process, we can generate either errors or warnings, and they get attached to the eventual `Response`. In some cases, we may want to short-circuit the normal flow and return an error response immediately (e.g., if a route handler raises an exception). In other cases, we may want to accumulate warnings and send them along with a successful response. Regardless, the `BridgeClient` will be responsible for displaying these messages to the user in a consistent manner.

How are streaming responses handled? How are long-running tasks handled? In both cases, we can yield `Progress` payloads from route handlers, which will be sent to the `BridgeClient` as they are generated. The `BridgeClient` can then update the page to show progress indicators or partial results as they come in.

From the student developer's perspective, they are building a `Site`, which can have multiple `Route`s. A `Route` is a decorated function that takes in the current `State` and any relevant parameters, and returns a `Page` (or other `ResponsePayload`). A `Site` also has metadata like title, description, favicon, language, etc.

A `URL` is a string that represents a unique `Route` function in the `Site`. It should follow the naming conventions of a Python function (e.g., lowercase letters, numbers, underscores, no spaces or special characters). Eventually, we might support slashes for things like classes or modules (which would probably translate to periods).

Things that have to be kept in the server:

-   State
-   Initial state (for resetting)
-   Accessed pages, args
-   History of state

The debug information present in the frame:

-   Quick link to reset the state and return to index
-   Link to the About page
-   Status information:
    -   Any errors and warnings, nicely formatted
    -   Current route information
    -   Request/Response dump
    -   Current state dump, buttons to save/load state in localStorage or download/upload JSON
    -   Current page information
    -   All available routes
        -   As a flat list
        -   As a graph
    -   Page load history
        -   Pages, state, args, timestamps, etc.
        -   VCR playback controls
        -   Automatically produced tests
    -   Test status information
    -   Button to activate codemirror instance that let's us do a REPL type thing?
-   Test production button
-   Compile site button

The `Monitor` tracks information about the server's behavior (and some amount of information from the client), and is a centralized place to log telemetry events for analysis.
Telemetry entails logging events like page loads, errors, warnings, state, performance metrics, user interactions, etc. Essentially, any debug information from the server should
be logged as telemetry events.
These TelemetryEvents are then transformed into other representations as needed: raw information to be printed on stdout, logs for storing on disk, analytics for displaying in the debug panel.

Essentially:

-   The `BridgeClient` handles all DOM manipulation and user interaction on the client side.
-   The `ClientServer` processes requests, manages state, and generates responses on the server side
-   The `Page` (and other `ResponsePayload`s) represent the content and structure of the pages being served, and are created by the user-developer.
-   The `Request` wraps user interaction data for transmission from client to server, and is created by the `BridgeClient`.
-   The `Response` wraps the `ResponsePayload` with metadata for transmission between client and server, and is created by the `ClientServer`.
-   The `Outcome` wraps the result of processing a response for transmission from client to server, and is created by the `BridgeClient`.

How is `open` and `read` handled? We need to determine all of the local file dependencies of the project. The user should be able to provide an explicit list, but otherwise we assume that adjacent files will be possible to include. Starlette can load these files dynamically, but for deployment we need to make sure they get provided such that they can be opened.

Images will assume to be available via the server.

## Development: watch JS assets

To iterate on the JS client and have changes flow into the Python package automatically:

1. In one terminal, run the JS watcher (this rebuilds on every save and copies the output into `src/drafter/assets`):

```powershell
cd js
npm install
npm run dev
```

2. In another terminal, run a local Drafter app so you can see live reloads. For example, using one of the examples:

```powershell
python examples\simplest.py
```

Notes:

-   The watcher writes bundles to `src/drafter/assets` which the dev server serves from `/assets` and is already included in the server's file-watcher, so connected browsers will auto-reload.
-   If you maintain a local Skulpt build, set `SKULPT_DIR` in a top-level `.env` to copy `skulpt.js` and `skulpt-stdlib.js` directly into `src/drafter/assets` on startup (`npm run dev` calls this automatically).

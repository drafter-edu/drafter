---
page_type: concept
title: Architecture
audience: D
priority: P1
prereqs: []
symbols: []
outcome: Understand the system design.
search:
  exclude: true
---

# Architecture

This page is the one-sitting orientation. The authoritative,
detailed document is `ARCHITECTURE.md` at the repository root;
when the two disagree, that file (and above it, the code) wins.

## In one sentence

Drafter is a Python library whose "server" is a pair of objects
living inside the visitor's browser: a deliberately ignorant DOM
bridge and a client server that owns all the logic.

## The idea

**Three run modes.** `start_server` (`src/drafter/launch.py`)
dispatches on where it finds itself:

1. **Web mode**: running inside Pyodide in a browser. This is
   where the real app lives; `run_client_bridge` wires up the
   `ClientBridge` and `ClientServer`.
2. **Compile mode**: `compile_site`
   (`src/drafter/builder/build.py`) emits a static site for
   deployment.
3. **App mode**: ordinary CPython. A Starlette/uvicorn dev
   server (`src/drafter/app/app_server.py`) serves a single
   "true page" that boots Pyodide, ships the student's source to
   it, and reruns the program there. Hot reload rides a
   WebSocket watched by `watchfiles`.

The student-visible consequence is the two-run model: top-level
code executes once in CPython (tests, prints) and again in the
browser, where `start_server` becomes the wiring call.

**The bridge/server split.** In the browser, two objects divide
the work:

- The **ClientBridge** (`src/drafter/bridge/`) touches the DOM:
  it renders content it is handed, collects form values, listens
  for events, and reports them. It is kept deliberately stupid
  about what the site means.
- The **ClientServer** (`src/drafter/client_server/`) owns
  routing, state, history, and testing. It receives request-like
  messages from the bridge and answers with response-like
  payloads. It is not a network server; it is a class the bridge
  calls.

The default instance is the lazily created module-level
`MAIN_SERVER` (`client_server/commands.py`); a registry supports
multiple independent embedded apps on one page, which is how the
documentation's own demos work.

**Components and rendering.** Student code builds component
trees (`src/drafter/components/`); each component produces a
`RenderPlan` describing its tag, attributes, and children.
Custom-element components (Timer, Map, Camera, and friends)
render as `<drafter-*>` tags whose behavior lives in TypeScript
(`js/src/components/`), with a Python-side `ComponentContract`
declaring the events they emit and the payload fields routes may
receive. Capture-style components keep a hidden form field
(`data-transform="json-decode"`) updated with their value, so
route parameters receive them through the normal form pipeline.

**Parameters and conversion.** The router
(`src/drafter/router/`) matches submitted form fields to route
parameters by name and converts values using the parameter's
annotation, through a registry of converters (scalars, datetime
types, files, images, the map/location dataclasses). Friendly,
two-tier error messages (`src/drafter/data/error_explainer.py`)
are a design commitment, not a nicety.

**DOM structure.** `src/drafter/site/site.py` is the single
source of truth for element ids, all suffixed `--`. User content
renders inside `#drafter-body--`; the debug panel
(`#drafter-debug--`, TypeScript under `js/src/debug/`) is a
sibling of the form, which is why styling `body` leaks into the
debugger but styling the app container does not.

## See it

The life of one button click, in web mode:

```text
visitor clicks Button("Feed", "feed")
  -> ClientBridge catches the submit event,
     collects form fields (applying data-transform decodings)
  -> ClientServer receives the request envelope
  -> router resolves the "feed" route, binds state + parameters
     (converting values per annotations)
  -> the route function runs; returns Page / Fragment / Update /
     Redirect
  -> ClientServer records history, runs verification,
     answers with a response payload
  -> ClientBridge patches the DOM (full page or targeted
     fragment), notifies the debug panel
```

Nothing in that loop crosses a network.

## What this means for your code

- Logic belongs in the ClientServer side; the bridge should stay
  ignorant. If a change makes the bridge understand site
  semantics, it is probably in the wrong place.
- New custom-element components must keep their TypeScript
  implementation in sync with the Python `ComponentContract`;
  the contract is what the router trusts.
- The `--` id suffix and `DRAFTER_TAG_IDS` are the only
  sanctioned way to reference structural elements.
- The two-run model means library code cannot assume it is in a
  browser or in CPython; check with helpers like `is_pyodide()`
  rather than importing browser-only modules at module load.

## Where people get confused

- The dev server in app mode serves the page and the source; it
  does not run routes. All routing happens in the browser, which
  is why "server logs" for route calls do not exist.
- `ClientServer` responses look like HTTP but never touch a
  socket; grepping for a web framework in the request path finds
  nothing because there is none.
- Skulpt appears throughout the codebase as a second engine. It
  is legacy, semi-supported, and outside the validation
  baseline; Pyodide is the default and the future.

## Go deeper

- `ARCHITECTURE.md` at the repository root: the full document
  (configuration system, builder, persistence, multi-instance
  embedding, hosting).
- [Writing documentation](docs-guide.md): the docs pipeline,
  which exercises the multi-instance embedding.
- [Python in the browser](../extend/pyodide.md): the
  student-facing version of the runtime story.

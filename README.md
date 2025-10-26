# Websites

A simple Python library for making websites

## Organization

If a user runs the program directly, then when it reaches `start_server`, it will start a local development server using Starlette.
This server will serve a single page that sets up Skulpt and a hot-reload connection to the server.
That page will also load the Drafter client library.
Finally, the page will also load the user's code into Skulpt and run it.
Effectively, this is running the program twice. The first time is "server side" with no real implications (other than starting the server, unit tests, print statements, etc.).
The second time is "client side" in Skulpt, where the user's code is actually run.
Images will assume to be available via the server.

If the program is then run via Skulpt, the Drafter client library will set up the page content.

If the `build` command is used, then it will instead generate static HTML, CSS, and JS files that can be deployed to any static hosting service.
The main `index.html` file will set up Skulpt and load the user's code into it, as well as load the Drafter client library to set up the page content.
It will try to precompile the library to populate as much meta information as it can, as well as an HTML preview that can be shown for SEO contexts.

We need to determine all of the dependencies of the project. The user should be able to provide an explicit list, but otherwise we assume that adjacent files will be possible to include.

## Drafter Client Library

This sets up the initial page structure and runs the user's code in Skulpt to generate the landing page.
The actual `start_server` is what sets up the page content.

Internal links and buttons will call the Skulpt functions to get the new content.

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

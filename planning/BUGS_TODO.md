# Bugs found during the November 2026 docs review

These are library problems noticed while checking every claim in the student docs against a running site. None of them is fixed here. The docs pass only wrote around them, and each item names the pages that describe the current behavior so they can be corrected with the fix.

How they were found: Drafter 2.2.1 source on 14 November 2026, Windows 11, headless Chromium driven by Playwright against the dev server and against compiled sites. Line numbers are from that source and will drift.

Each item ends with how well it is established:

- **(browser)** seen in a real page.
- **(ran)** reproduced by running Python, with no browser.
- **(source)** read in the code only.
- **(unconfirmed)** seen once or not diagnosed. Reproduce it before fixing.

Some items overlap with `post_hackathon26_items.md`; those say so.

# Students will hit these

- [ ] **Reloading the tab after a form submit shows an error page.** The address bar keeps `?route=<last route>`. A reload resets the state and runs that route again with no form values, so a route with a required parameter stops with "Problem With the Route's Arguments" ("expects a value for parameter 'new_name'"). "Return to Index Page" recovers. Same on the dev server and on a compiled site. Related: values in the address are never passed along, so `?route=greet&who=Ada` and `/greet?who=Ada` both run `greet` without `who`. Possible fixes: fall back to `index` when the reloaded route is missing required arguments, or keep `?route=` off requests that carried form data. Docs: `docs/help/troubleshooting.md` ("Reloading the tab does not go back to the first page"), `docs/help/faq.md`, `docs/reference/route.md#opening-a-site-on-a-route`. (browser)
- [ ] **"Reload Entire Application" on an error page never settles.** The link goes to `--reload`, the address keeps `?route=--reload`, and every load runs it again: 22 reloads in 30 seconds with browser history on. Opening `?route=--reload` directly does the same. Docs: `docs/reference/route.md#built-in-routes` says only that `--reload` is not meant as a button target. (browser)
- [ ] **`Download` with text content damages the file.** `components/files.py:102` builds `data:<type>,<content>` without escaping. A `#` ends the file there, `%41` arrives as `A`, and trailing whitespace or a final newline is dropped. Bytes content arrives intact. Percent-encoding or base64 would fix it. Docs: the Notes bullet in `docs/reference/components/input/download.md`, and the save-and-load recipe in `docs/add/files.md`, which calls `.encode("utf-8")` to avoid this. (browser, Chromium only)
- [ ] **Many input keywords silently become CSS.** A keyword missing from a component's `KNOWN_ATTRS` is rendered as a style, for example `style="max: 10; min: 0; required: True"`, so `TextBox("age", kind="number", min=0)` has no lower bound and nothing warns. Missing keywords by component (`components/forms.py`, `components/files.py:140`):
    - `TextBox`: `required`, `min`, `max`, `step`, `disabled`, `readonly`, `autocomplete`, `list`
    - `TextArea`: `maxlength`, `minlength`
    - `SelectBox`, `ColorPicker`, `FileUpload`: `disabled`
    - `CheckBox`, `RelatedCheckBox`: `required`, `disabled`
    - `DateInput`, `DateTimeInput`, `TimeInput`: `min`, `max`, `step`, `required`, `disabled`, `readonly`
    - `Slider`: `disabled`, `list`
    - `RadioButtonGroup`: everything. `KNOWN_ATTRS` is empty and keywords land on the wrapper `div`.

    Two connected problems. Browser form validation never runs on a `Button` click, so even the recognized `required`, `pattern` and `minlength` do not stop the route (`maxlength` does limit typing). And `autocomplete` is in `BOOLEAN_ATTRS`, so `TextArea(autocomplete="off")` renders a bare `autocomplete`. Docs: every page under `docs/reference/components/input/` now lists the attributes that work. (ran and browser)
- [ ] **A missing local module is installed from PyPI by name.** When `import helpers` finds no `helpers.py` beside the program (typically a file that was never uploaded to the deployed site), the browser installs the unrelated PyPI package called `helpers` and the student gets a confusing error from that package. A message saying the local file is missing would help. Docs: the deployed-import entry under Common problems in `docs/add/files.md`. (browser)
- [ ] **A tab left from an earlier run never reconnects.** After the same file is run again and takes over the port, the old tab keeps running the old code, ignores saves, and says nothing. There is no reconnect for the dev websocket (`js/src/pyodide.index.tsx:570-572`). Either reconnect, or have the takeover message tell the student to reload the tab. Docs: `docs/help/troubleshooting.md` ("The browser shows an old or different app"), `docs/start/make-a-change.md`. (browser)
- [ ] **A button that points at a missing route gets a confusing error page.** The title is "Unusable Value", the generic title for a `ValueError`. The message calls the button a "Link" (`components/links.py:187-197`; already in `post_hackathon26_items.md`). The hint says to pass the route function itself, which the docs do not teach and which raises `NameError` when a test runs above the target's definition. The same generic title is used for Drafter's other untitled student errors: page content, a `SelectBox` default that is not an option, and a bad `Header` level. Docs: `docs/start/make-a-change.md` quotes the current text, and so does `docs/help/errors/route-not-found.md`. (browser)
- [ ] **Unused values fill the debug panel with warnings.** Every form field on a page warns for any route that does not take it ("The form field 'X' was sent to 'Y', but the function has no matching parameter."), including a Cancel button on a form page. Event values do the same: the docs' own `Timer` example, `times_up(state)`, produces two warnings each time it finishes ("The event value 'duration' was sent to..."). Already in `post_hackathon26_items.md`. Docs: `docs/help/errors/missing-parameter.md` explains the warning. (browser)
- [ ] **When `drafter.pyodide.js` fails to load, the page looks ready but is dead.** The loading screen is removed, the buttons do nothing, and the only message is a `TypeError` in devtools. (browser)
- [ ] **`input()` in a route shows a browser prompt with no question.** The text passed to `input` is not shown. (browser)

# Settings and the command line

- [ ] **Config files crash.** `--config-file` and `DRAFTER_CONFIG_FILE` end in `RecursionError` before anything starts, through `drafter`, `python -m drafter` and `python main.py`. `BaseConfiguration.load_from_file` (`config/base.py`) calls the patched `builtins.open` (`files/opening.py:181`), which calls `get_system_configuration()` while the configuration is still being built. Docs: config files were left out of `docs/reference/start-server.md#where-settings-come-from` and removed from `docs/reference/live-reload.md`. (ran)
- [ ] **Six environment variables are ignored.** `DRAFTER_PORT`, `DRAFTER_HOST`, `DRAFTER_USE_RELOADER`, `DRAFTER_OPEN_BROWSER`, and the ones for `inline_py` and `serve_adjacent_files` are always overwritten by argparse defaults (`config/app_server.py:189-225`). The watch flags use `default=None` and work. Docs: `docs/reference/start-server.md` and `docs/reference/live-reload.md` say these have no effect. (ran; `DRAFTER_HOST` source only)
- [ ] **`DRAFTER_FRAMED=false` leaves the frame on.** The value is read as a string (`config/client_server.py:187`), so `"false"` is truthy. (source)
- [ ] **`--zip-output` does nothing.** The flag is accepted and `zip_output` is stored, but the builder never reads it. Docs: the row was removed from `docs/reference/cli.md`. (ran)
- [ ] **`--reset` resets the main server, not the one handling the request.** `router/defaults/reset.py:16-17` calls `get_main_server()` and has a TODO about it. A normal single app works. With a second `ClientServer` the state is not reset, which probably includes embedded docs demos. Docs: the "Start over" example in `docs/reference/route.md` is a plain fence for this reason. (ran)
- [ ] **A misspelled `start_server` keyword is ignored silently.** No terminal message and no debug-panel warning. Docs: `docs/reference/start-server.md` warns about it. (browser)
- [ ] **A configuration function and a `start_server` keyword that disagree give a split result.** The tab title and debug panel followed the functions while the theme followed the keyword. (browser)
- [ ] **`set_website_style("water")` on its own leaves an error in the debug panel**: "Drafter had trouble syncing your Python code with the browser" / "Could not apply the new theme to the page", although the theme is applied. This is the same symptom as the almond item in `post_hackathon26_items.md`. (browser, headless Chromium; unconfirmed elsewhere)
- [ ] **The port check misses some occupied ports on Windows.** With `python -m http.server 8136` running (bound to `::`), `main.py --port 8136` started with no message and both listened on the port. `port_is_free` in `app/ports.py` is a plain bind test and only caught an occupant bound to `127.0.0.1`. (ran)
- [ ] **`add_website_file` reports problems badly.** A missing file named at module level shows a raw traceback, so the friendly "Did you mean" steps are never seen. Wrong letter case is not detected on Windows, and the copy takes the spelling in the code. A folder name is rejected as "file not found". Docs: `docs/reference/site-config.md` promises suggestions. (ran)
- [ ] **`set_assertion_defaults(True)` is accepted positionally and sets `precision=True`.** (ran)
- [ ] **The takeover shutdown message is wrong.** When a new run stops an earlier one, the earlier one prints "Stopping the server because the browser asked it to." (ran)

# Components, pages and tests

- [ ] **Every `Link` renders `style="name: --submit-button"`.** `name` is set at `components/links.py:270` but is missing from `Link.KNOWN_ATTRS` (line 232). (ran)
- [ ] **`RadioButtonGroup.get_id` returns the default value.** The wrapper renders `id="medium"`, or `id=""` with no default. (ran)
- [ ] **`data-nav` or `data-call` on anything but a button or anchor throws on click**: "Failed to construct 'FormData': The specified element is not a submit button". `bridge/events.py:313-319` passes the element as the submitter. A `<span data-nav="route">` inside `RawHTML` is enough to trigger it. (browser)
- [ ] **Forgotten brackets around page content give a poor error.** `Page(state, "Hello", Button(...))` fails at render with `AttributeError: 'Button' object has no attribute 'extend'`, because the third positional argument is `css`. `Page(state, "Hello", "there")` is accepted silently and "there" is treated as CSS. (ran)
- [ ] **`Header(2, "Title")` gives "Type Mismatch"** ("'<' not supported...") in place of the header-level error, and `Header("Title", 2.5)` is accepted. (ran)
- [ ] **`assert_children(BulletedList(["a", "b"]), ["a", "b"])` fails** with "Too few items (1 < 2)", although the docstring names `BulletedList` items as the use case. (ran)
- [ ] **The two state-type checks disagree.** `SiteState.update` warns when `type(a) is not type(b)` (`history/state.py:119`), while verification uses `isinstance` (`payloads/verification.py:215`). A subclass of the state class, or an `int` state replaced by `True`, passes verification and then logs the warning. Docs: `docs/help/errors/state-mismatch.md` covers it as a second case. (ran and browser)
- [ ] **Empty values and optional parameters are inconsistent.** An upload with no file chosen gives `''` for `str | None` but `None` for `Picture | None`. An empty text box is an error for `int | None` and for a parameter with an `int` default. Empty text for `date`, `time` or `datetime` gives the current date and time. Docs: `docs/reference/route.md#parameter-conversion`, `docs/add/files.md`. (ran; uploads in browser)
- [ ] **Code after `start_server()` runs in the browser but not on the computer.** It prints once in the page's Console box and never in the terminal. Docs: `docs/start/how-drafter-works.md` says "On your computer, nothing after it runs." (browser)
- [ ] **Site-wide JavaScript piles up on live reload.** `add_website_js` code runs again on each save in the same document, so listeners accumulate. One key press advanced several cards after a save. Docs: `docs/extend/javascript.md` shows a guard variable. (browser)
- [ ] **A missing image produces no warning.** A plain broken `<img>`, no error page, nothing in the debug panel. The dev server's terminal shows the 404. (browser)
- [ ] **`assert_equal` may report the wrong line.** It printed "SUCCESS at line 141" for a 31-line script run from outside the repository. (unconfirmed)

# Error messages

- [ ] **"a int".** "returned a int" and "is a int" in `payloads/verification.py:91` and `:227`. (ran)
- [ ] **The missing-parameter page repeats itself.** The "What To Try Next" item is the technical message word for word. (browser)
- [ ] **`import turtle` and `import tkinter` get the wrong advice.** The dialog's steps say to check the spelling and that Drafter "looked for a library named `turtle` to install". These are standard-library modules that the browser's Python leaves out. Docs: `docs/help/errors/package-import-error.md` leads with this case. (browser)
- [ ] **The "Error" dialog stays open after the fix.** Once the file is corrected and the site has reloaded, the dialog from the failed run is still showing. (browser)
- [ ] **A failed reload logs a second error in the console**: "[Drafter System Error] Failed to deliver system error to debug panel Error: DebugPanel: drafter-debug-log content not found." (browser)
- [ ] **Generated regression tests contain HTML for circular references.** The route call has `owner=<strong>Circular Reference</strong>` and the expected page has `owner=...`, so the pasted test fails. Docs: `docs/help/errors/circular-reference-tests.md`. (ran)
- [ ] **A failed snapshot load shows the generic text** "One of the values in your code had the right type, but its content was not something Python could use there." The specific message about a snapshot "saved under a different version of your code" is never shown. (browser)
- [ ] **An `async def` route says only that it "returned a coroutine instead of a Page".** The message could say that routes cannot be `async`. Docs: `docs/extend/javascript.md#waiting-for-a-javascript-promise`. (browser)

# Debug panel

- [ ] **Unfinished features are visible to students.** Edit > "Edit State..." opens a "coming soon" dialog (`js/src/debug/state_edit.tsx`). The Overview tab's route graph is a hardcoded drawing of `index / guess / give_up / result` for every app (`js/src/debug/panels/route_graph.tsx`). Environment > Advanced ("Show Drafter internals") presents sample numbers. Runtime Info has "(coming soon)" rows for Memory and Uptime. The Host File System list stayed empty after Refresh. Docs: `docs/help/debug-panel.md` and `docs/start/debug-panel.md` describe these as unfinished. (browser)
- [ ] **Loading a snapshot re-runs the saved route.** A snapshot saved on a route that changes the state loads one step ahead: saved at 1 on `add`, loaded as 2 (`bridge/client_bridge.py:346-399`). (browser)
- [ ] **Snapshot slots are shared between apps.** They are keyed only by slot name in `localStorage` (`drafter.debug.snapshot.v1.<slot>`), so every app served at the same address sees the same slots. (browser)
- [ ] **Three labels do not match what happens.** Navigate > Reset says "Clear state, history, and return to home", but the History tab keeps its visits. The Console's Hide tooltip says the box stays hidden "until new output is printed", but new output does not reopen it. Stop Server warns that "this tab will stop working", but the loaded page keeps responding to clicks. (browser)
- [ ] **"Compare with previous state" may do nothing.** Clicking it produced no dialog that the test script could find. (unconfirmed)

# Documentation site

- [ ] **Docs demos hide `print` output.** The plugin passes `--console_mode hover` (`src/drafter/docs/mkdocs_plugin.py:317`). The real flag is `--console-mode`, argparse ignores the misspelling, and demos run in `auto` mode with debug off, so output appears only after the demo's "debug" button is clicked. Docs: notes in `docs/start/debug-panel.md` and `docs/help/printing-and-console.md` that can go once this is fixed. (browser and source)
- [ ] **A demo's `js.document` is the docs page.** All demos on a page share one Pyodide hosted by the parent page, so a demo cannot find its own elements by id and `focus()` in a demo scrolls the docs page. This is why the `Canvas` example and four recipes in `docs/extend/javascript.md` are plain fences. (browser)
- [ ] **Text typed into a demo right after it appears can be lost.** A value typed about half a second after first paint reached the route as an empty string, twice out of twice. With a wait of 2.5 seconds or more it usually worked. (unconfirmed, not diagnosed)

# Docstring and docs leftovers

- [ ] The friendly text for a failed date or time conversion and the `Fragment` docstring still say content "Must always be provided as a list", and `Page.verify` keeps unreachable branches for "content given as one plain string".
- [ ] `docs/reference/components/input/fileupload.md` types `accept` as `str`. The source also takes a list and adds the leading dot.

# Fixed the same day (2.2.2)

Found in this review and already fixed, listed so they are not reported again:

- `--external-pages "dashboard/ Dashboard"` rendered a link whose address and text were both the whole string.
- `set_site_information` and `set_browser_history` put "Unhandled configuration update event" in the debug panel.

# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Fixed charts drawn in unit tests showing up in the first page with a `MatPlotLibPlot` (#149). A test calls the route and compares the page without displaying it, so the chart it drew stayed open and the next chart was drawn on top of it. `MatPlotLibPlot()` now takes hold of the current figure when it is created, and (unless `close_automatically=False`) closes it right then, so the next chart always starts blank. This also fixes charts piling up between page visits in the browser, where the figure was never closed. Write your `plt.` commands before `MatPlotLibPlot()`; commands that run after it belong to the next chart.
- New wheel indexes for packages PyPI only has as source. Drafter's own index at `https://drafter-edu.github.io/packages/wheels.json` (ChemPy and its supporting packages) is searched whenever PyPI has no wheel for a package, so `import chempy` works in the browser with nothing to configure. An index is installed as a set, and the set's remaining declared requirements (such as `sympy`) are then fetched from the browser's own distribution or PyPI. Courses can add their own indexes with `--package-index URL` (repeatable; `DRAFTER_PACKAGE_INDEXES`, `package_indexes`), searched before Drafter's, and leave Drafter's out with `--no-default-package-index` (`DRAFTER_USE_DEFAULT_PACKAGE_INDEX`, `use_default_package_index`).
- Libraries outside the browser's built-in set now install by themselves (#203). `import seaborn` used to stop with `ModuleNotFoundError` in the browser, because automatic package loading only covered libraries bundled with the browser's Python (like `matplotlib` and `pandas`). Drafter now also looks up every other imported name on PyPI and installs it before the program runs. Your own files always come first: a `utils.py` next to your program is never replaced by a PyPI package of the same name. `--no-load-packages-automatically` turns this off along with the rest of automatic loading.
- When an `import` still fails in the browser, the error page names the library and lists the likely causes: a misspelling, a library that installs under a different name (declare it with `--project-packages`), or one that cannot run in a browser.
- New guide, "Use a CSS framework" (#218), shows how to style a Drafter site with Bootstrap or Tailwind class names: turn the theme off with `set_website_style("none")`, then load Bootstrap's stylesheet with `add_website_css_file` or Tailwind's version 4 browser script with `add_website_js_file`. No new functions were needed. The older `cdn.tailwindcss.com` script is not recommended, because it leaves the first page unstyled until the visitor clicks something.
- New guide, "Use pytest or unittest" (#8), shows how to test a Drafter site with either tool: set `DRAFTER_SKIP` before importing the site file so `start_server` does nothing, then call routes and compare pages with plain `assert` or `self.assertEqual`. It also shows how to keep Drafter's own assertions inside those tools. The guide's code is run by Drafter's test suite, so it stays correct.
- The debug panel's History tab shows one line per visit (#175): how it went (Success, 1 warning, Error, Page not found), the time, the call as you would write it (`save(size=60, name='Ada')`, with pictures and files summarized), how long it took, and the first warning or error. Expanding a visit lists where each argument came from and what it was converted to, with thumbnails for pictures and swatches for colors. Pages are gone: ten visits show, and a "Show older visits" button adds more without losing your place.
- Errors are reported once (#174). The browser runtime now recognizes an error it has already reported when the same error reaches a later layer or the browser's own error event, so a single failure no longer appears twice. Errors that escape to the browser unreported (an uncaught exception in a callback, a failed background task) now reach the debug panel. When the same problem repeats, the Current tab and the Log tab show a counter such as ×3 instead of another line, and the `drafter-debug.log` file records a repeat count rather than a copy per repeat (at most three entries per problem per session).
- The browser tab's title now starts with the number of errors and warnings on the current page while there are any, so a problem is visible from another tab.
- New **Convert HTML to Drafter…** item in the debug panel's Edit menu (#216). Paste HTML or choose an `.html` file and it writes the matching Drafter components and `add_website_css` calls for you to copy. The converter is downloaded the first time it is used, so pages that never open it are not slowed down.
- `ColorPicker` accepts its starting color in any common spelling: a hex code (`"#ff8800"`), a short hex code (`"#f80"`), any of the 148 browser color names (`"tomato"`), a list or tuple of red, green, and blue amounts (`[255, 136, 0]`), or the new `Color` value. A misspelled color name gets a suggestion. `ColorPicker(name, color, alpha=True)` adds an opacity slider beside the swatch, and the color then carries an alpha amount.
- New `Color` data type with `red`, `green`, `blue`, and `alpha` fields, each a whole number from 0 to 255 (the same scale as a `Picture`'s pixels). Annotate a route parameter as `Color` to receive a picked color that way, or as `list[int]` to receive the amounts as a list; `str` still gives the hex code. A `Color` can be passed anywhere Drafter takes a color, such as `style_color`. `Color.from_hex` and `Color.from_name` build one from text.
- Fixed two wrong hex codes in the color name reference (`mediumpurple` and `palevioletred`).
- New `Slider` and `ColorPicker` input components (#28). `Slider(name, min, max, default_value=None, step=1)` shows a track with a draggable handle and sends the chosen number to the route; annotate the parameter as `int`, or `float` when `step` is a fraction. `ColorPicker(name, default_value="#000000")` opens the browser's color chooser and sends the color as a hex code such as `"#ff8800"`, which works anywhere Drafter takes a color. Both check their arguments when created and explain mistakes (a `min` that is not below `max`, a starting value outside the range, a color name where a hex code is needed) instead of letting the browser silently substitute a default. The HTML-to-Drafter transpiler maps `<input type="range">` and `<input type="color">` to them.
- A stylesheet that fails to load is no longer silent (#232). When the browser cannot fetch a theme file or a stylesheet added with `add_website_css_file`, a notice at the top of the site says that some styling did not load and names the file, and the debug panel shows a warning that stays visible across pages. The notice has a Dismiss button and appears in deployed sites too, where it is the only sign of what went wrong.
- New `set_state_display(False)` turns off the debug panel's display of the application state (#171), for sites whose state is large enough that describing it after every change is slow or crowds the panel. The Current State section shows a one-line note instead. Only the display changes: the state itself, the back and forward buttons, and Save/Load keep working. Also available as the `state_display` setting, the `--no-state-display` command line flag, and the `DRAFTER_STATE_DISPLAY` environment variable.
- Building a site (`--compile`) that never calls `set_site_information` now prints a notice explaining that its about page will be empty, with the call to add (#183). The site is still built. On GitHub Actions the notice also appears as a warning on the workflow run's summary page. The `warn_missing_info` builder setting, which existed but did nothing, now controls this; turn the notice off with the new `--no-warn-missing-info` flag or `DRAFTER_WARN_MISSING_INFO=false`.
- Fixed `MatPlotLibPlot` writing its image into the `style` attribute instead of `src` when a page was rendered outside the browser.

## [2.1.4] - 2026-11-09

- Fixed sites failing to start after upgrading Drafter, with `TypeError: Failed to fetch dynamically imported module: .../pyodide.asm.js`. The browser could keep using the copy of Drafter's JavaScript it had saved from the older version, which then asked for a Pyodide file that newer Pyodide versions no longer have. Pages now load Drafter's scripts from addresses that include the Drafter version (such as `drafter.pyodide.js?v=2.1.4`), so each release gets fresh copies, and the local development server tells the browser to check Drafter's own files for changes before reusing saved ones. On an older version, a hard refresh (Ctrl+Shift+R, or Cmd+Shift+R on a Mac) clears the error.
- When the browser cannot download Python (Pyodide) or its packages, the error page now explains that in plain language instead of leading with a raw `TypeError`. It says the student's code is not at fault and lists what to try: check the internet connection, hard refresh the page, or try a different network, naming the server that could not be reached (school and work networks sometimes block it). The original error is still shown under Technical Details.

## [2.1.3] - 2026-10-20

- The local development server now opens the site in Chrome when it is installed, then Firefox, and only then the computer's default browser, so a fresh Mac no longer lands in Safari. A new `browser` setting picks a specific browser instead: `start_server(browser="firefox")`, the `--browser` command line flag, the `DRAFTER_BROWSER` environment variable, or a config file entry under `app_server`. Accepted names are `chrome`, `firefox`, `safari`, `edge`, `default` (the computer's usual browser), or any name Python's `webbrowser` module knows. A browser that cannot be found prints a warning and falls back to the default.
- The local development server can now be stopped from the browser. The debug panel's Navigate menu ends with **Stop Server…** (it asks for confirmation first), and the new `--stop-server` system route shows a confirmation page with the same button, so `http://localhost:8000/--stop-server` works directly. Stopping ends the Python program the same way as Ctrl+C in the terminal. The control only appears while the site is served by the development server; deployed sites have no server to stop. Behind the scenes this is a POST-only `__drafter_stop_server` endpoint, so a plain link or prefetch can never stop the server.
- Running a program while an earlier run is still using port 8000 no longer fails with a bare operating-system error while the old run keeps serving. Drafter now checks the port before starting: an earlier run of the same file is stopped automatically (through the new stop endpoint) and the port is reused; when another program, or a run that is stuck, holds the default port, Drafter moves to the next free port and prints the new address; a port chosen with `--port` or `port=` is never moved, and instead a student-facing error names what is using it and how to stop it. The development server also gained a `__drafter_status` endpoint, which a new run uses to recognize an earlier Drafter run and which reports the version, main file, and process id.
- Errors that stop the local development server before it starts (a busy port, a missing main file) are now printed in the terminal as a titled explanation with numbered "What to try" steps and a one-line technical detail, instead of a Python traceback. Running with `--verbose` (or `verbose=True`) restores the traceback.

## [2.1.2] - 2026-10-19

- Fixed auto-play audio and media (`Tone`, `Melody`, `Sound`, `Audio`, `Video`) never starting when a route returned it inside a `Fragment`, such as a piano key that plays a hidden `Tone(note, auto_play=True, show=False)` into an `Output` area. The `drafter-page-loaded` event now fires after Fragment updates too, with a new `fragment` field in its `detail` (true for Fragment updates, false for full page loads) so listeners can tell them apart.
- Fixed the first auto-play sound after a click staying silent, which also made the next click play the previous sound late. Auto-play components now start the browser's audio right away when the browser allows it (normally once the visitor has interacted with the page). If the browser is still blocking sound, the "Enable sound" prompt now appears even for components with `show=False`, instead of being hidden.
- Fixed importing a local package (a folder with an `__init__.py`, as in projects set up with a `pyproject.toml`) crashing in the browser with `ModuleNotFoundError` even though it worked in regular Python. Packages, their submodules, and relative imports inside them now load in the browser just like single-file modules.

## [2.1.1] - 2026-10-10

- Fixed the `--about` pages and `create_404` settings

## [2.1.0] - 2026-08-23

- New `add_website_css_file(path)` and `add_website_js_file(path)` link a stylesheet or script into every page, from a file next to the student's program or a full URL, alongside `add_website_js(code)` for inline JavaScript (matching `add_website_css`). New `add_website_file(*filenames)` declares other files the site needs (data files, images, fonts). Files next to the program are validated as soon as the call runs: a missing file raises a student-facing error that names the folder searched and suggests similarly named files (a capitalization slip, a different extension, a typo, or the same name in a subfolder); absolute paths, `..` paths, wrong extensions, and CSS/JS code passed where a file name was expected get their own explanations. `add_website_css`/`add_website_js` now catch a bare file name or URL passed as "code" and point at the `_file` variant. Registered files ship with `--compile` builds automatically, next to `index.html`. Also available as the `additional_css_files`, `additional_js_files`, and `additional_files` settings (`--additional-css-files`, `--additional-js-files`, `--additional-files` flags; `DRAFTER_ADDITIONAL_*` environment variables). Absolute URLs given to `additional_css_content` are no longer mangled by the assets-folder remapping, and external scripts (`additional_script_content`) are now actually loaded with `<script src>` tags. The client bridge now handles the replayed `site_title` and content-list configuration events instead of reporting "Unhandled configuration update event"; content added after `start_server()` is injected into the running page.
- New `browser_history` setting controls whether Drafter navigation is mirrored into the browser's history stack at all. Disable it (via `set_browser_history(False)`, the `--no-browser-history` command line flag, or the `DRAFTER_BROWSER_HISTORY` environment variable) when a Drafter app is embedded in another page, so the back button keeps navigating the host page instead of the app; the app's own history/replay debug tools keep working. Embedded multi-instance apps (such as the live demos in the documentation) disable it automatically.
- The browser's back/forward buttons now time travel: each history entry stores a snapshot of the application state as it was when that page was visited, and navigating back restores that state before re-running the route, reproducing the original page instead of replaying the route against the current state. Backing all the way to the first entry restores the app's startup state. Snapshots use the same no-pickle JSON encoding as the debug panel's Save/Load feature, so states that cannot be saved (or that no longer match the code after an edit) degrade gracefully to the old replay behavior with a warning.
- Page and Fragment content now accepts plain integers, floats, and booleans alongside strings and components; they render as their text form (e.g., `Page(state, ["Score:", state.score])` no longer needs `str()`). The "must be a list of strings or components" error message and its help page were updated to match ("must be a list of strings, numbers, booleans, or components").
- **Breaking (CLI):** List-valued command line options are no longer semicolon-separated; repeat the flag once per entry instead (e.g., `--additional-paths pets.csv --additional-paths words.txt` rather than `--additional-paths "pets.csv;words.txt"`). Affects `--external-pages`, `--additional-header-content`, `--additional-style-content`, `--additional-css-content`, `--additional-js-content`, `--additional-script-content`, `--project-packages`, `--system-packages`, and `--additional-paths`. The corresponding `DRAFTER_*` environment variables remain semicolon-separated, since an environment variable cannot be repeated.
- Fixed automatic package loading and explicit package lists being mutually exclusive: explicitly listed `--project-packages` are now installed in addition to (rather than only in the absence of) automatic import detection, matching the documented behavior. Added `--no-load-packages-automatically` to turn off detection and load only the explicitly listed packages, which was previously impossible from the command line.
- If used in thonny, should try to recover the source code if it's available. Otherwise, provides a friendlier error.
- Updated pyodide to new version
- More control over pyodide url/branch/release
- Live reload now runs safety checks before recursively watching the main file's folder. If the folder is a filesystem root, the home directory, a broad location (Desktop, Documents, Downloads, ...), or exceeds configurable size limits (`watch_max_files`, `watch_max_directories`, `watch_max_depth`), Drafter prints a notice and switches to a safe mode that watches the main file, explicitly configured paths, and files the site actually serves — instead of the entire folder. New `app_server` settings control the policy: `watch_adjacent_files`, `watch_recursively`, `watch_safe_mode`, `watch_served_files`, `watch_broad_locations`, `watch_paths`, `ignore_watch_paths`, `watch_manifest` (a JSON file listing project files/directories/globs to watch, optionally with ignores), and the `watch_force_recursive` escape hatch. Drafter-generated files (like `drafter-debug.log`) can never trigger reloads.
- Fixed `use_reloader=False` so the file watcher genuinely never starts.
- Fixed second double loop in app server that didn't let us auto launch browser.
- Rendering errors inside nested page content now report their location in the student's vocabulary instead of internal HTML tags: an unsupported value in a table cell says "the Table at index 1, row index 0, column index 1" rather than `At ['[1]', 'table', '[1]', 'tbody', ...]`, with advice tailored to the offending value (`None` suggests a missing `return`, a bare function suggests `Link`/`Button`, a tuple suggests a list, and so on). The full internal path is still available in the technical details. Components that raise a `StudentFacingError` while rendering also keep their friendly explanation instead of falling back to the generic "Type Mismatch" text.
- Fixed a race when an instance is reset (editor re-run, documentation demo restart) while a click or form submit is still in flight: the torn-down bridge could still dispatch that navigation afterwards, re-pinning the discarded server as the current one (so the next run's routes and `start_server()` silently attached to it) or re-rendering the old page over the new one. A torn-down bridge now drops any further navigation and popstate events.

## [2.0.3] - 2026-08-21

-   Restored the `DRAFTER_SKIP` setting from v1: when enabled, `start_server()` does nothing (no server, no compilation), so a site file can be imported by a unit test runner. Available as the `DRAFTER_SKIP` environment variable, the `--skip` command line flag, a config file setting (under `bootstrap`), or `start_server(skip=True)`.
-   Updated the deployment instructions to link the official deployment repository template ([drafter-deployment-template-v1](https://github.com/drafter-edu/drafter-deployment-template-v1/generate)).

## [2.0.2] - 2026-07-27

-   Fast bug fix for themes not getting built into released bundles, which caused the deployed site to not load correctly.

## [2.0.0] - 2026-07-27

-   Complete rewrite of the entire system. Deployment now happens through Skulpt or Pyodide, with no backend server required.
-   Matplotlib is no longer preloaded in the browser; it is installed on demand when student code imports it or uses `MatPlotLibPlot`.
-   New component system, with better attribute handling and more components.
-   More sophisticated architecture for handling state, navigation, and rendering.
-   Improved error handling and debugging tools.
-   New testing framework for writing and running tests against Drafter applications.
-   Added semantic inline text components: `Strong`, `Emphasis`, `InlineQuotation`, `DefinitionTerm`, `Abbreviation`, `DeletedText`, `InsertedText`, `KeyboardInput`, `MarkedText`, `SampleOutput`, `SmallText`, `Superscript`, `Subscript`, and `InlineVariable`.
-   Added structural components: `Figure`/`FigureCaption`, `Details` (with `summary`, `open`, and accordion-style `group`), and `DefinitionList` (accepts a dictionary, a dataclass instance, or a list of term/definition pairs).
-   Added `Meter` (with `min`/`max`/`low`/`high`/`optimum`) and `TimeOutput` (with `datetime`) output components.
-   Renamed the `Progress` component to `ProgressBar` to avoid overlap with the planned `Progress` payload type.
-   The HTML-to-Drafter transpiler now maps the corresponding tags (including `strong`, which previously produced `bold(...)`) to the new components.
-   Ported the `simple`, `skeleton`, and `tacit` classless themes from Drafter v1; all built-in themes now scope their layout to the Drafter frame so the debug panel is unaffected.
-   Ported the retro Windows themes (`98`, `xp`, `7`) from Drafter v1 as classless themes: the page now renders as a period-appropriate window on the desktop, with all element styling scoped to the Drafter body so the debug panel is unaffected.
-   Fixed the `sakura` theme squeezing the whole page (including the debug panel) instead of just the site content.
-   Added table styling to the `default` theme.
-   Warnings (and errors) without a request correlation, such as route-signature or state warnings raised at startup, now stay visible in the debug panel's Current-tab problems area instead of being wiped by the next navigation.
-   Added the `--bug-report` system route, which explains when a bug report is appropriate (actual Drafter bugs or limitations, not homework help) and provides a button that downloads the same bug-report bundle as the debug panel's Help menu.
-   Outside production mode, errors are now reported to the local development server and appended (with bug-report-style environment details) to a shared, size-capped `drafter-debug.log` JSON Lines file next to the student's code.

## [1.9.5] - 2025-12-05

* Images inside of Divs and other elements now have the correct path
* Fixed issue with images not rendering in test deployments.

## [1.9.4] - 2025-12-05

* Empty image uploads now provide a None value instead of an error
* D3 is now included in the deployed Skulpt version

## [1.9.3] - 2025-12-04

* The `Page` class now supports an optional `js` parameter to add custom JS to the page.
* File writing now works correctly in deployed Drafter (only writes to LocalStorage).

## [1.9.2] - 2025-12-02

* Fixed a related bug with deploying additional files

## [1.9.1] - 2025-12-02

* Fixed bug with deploying additional files

## [1.9.0] - 2025-11-30

* Footer can now be disabled (thanks to @BJT207)
* Documentation for using Drafter in VS Code
* New `set_server_setting` and `do_not_start_server` functions to control server settings
* Fix for `additional-files` cli option to correctly collect ALL files and not just the last one

## [1.8.9] - 2025-11-23

* Fixes for `repr` of rows, text, buttons, headers, and many other text elements.
* Explicit change for Gemini URL

## [1.8.8] - 2025-11-19

* Fixed issue with textbox contents not getting encoded correctly in the HTML
* Fixed issue with deploys defaulting to the old `'website'` directory instead of top-level
* Fixed the ability to control the deployment folder for images with `set_image_path` function
* Improved compatibility of new LLM Gemini call system with Skulpt
* Fixed issue with tables not testing correctly

## [1.8.7] - 2025-10-30

* Automatically make planning text into links for set_site_information
* Handle popstate in the deployed Skulpt version
* Fixed embarrassing but funny licensing issue

## [1.8.6] - 2025-10-10

-   Skip over non-text files when deploying through command line
-   Do not default to requiring site information to be set

## [1.8.5] - 2025-10-09

-   Fixed issue where multiple external pages were not being handled correctly on command line

## [1.8.4] - 2025-10-09

-   Fixed issue in the page navigation for Skulpt deployments

## [1.8.3] - 2025-10-09

-   Skulpt deployments now use Sk.bottle.changeLocation instead of window.location.

## [1.8.2] - 2025-10-09

-   404 redirects were not being processed
-   Deployed version should now register the CTRl+I shortcut for the about page.

## [1.8.1] - 2025-10-08

-   Minor issue with command line deployment fixed (drafter not runnable as a tool)

## [1.8.0] - 2025-10-06

-   Command line compilation of websites
-   Deploying through skulpt, the setup code stored in Drafter now
-   Script tags are properly escaped when the test deployment is launched.
-   About page now shows information using the `set_site_information` function
-   Command line flag for passing in external URLs

## [1.7.4] - 2025-08-08

### Added

-   Can now pass a single string into `Page`, and it will wrap it in a list automatically.

## [1.7.3] - 2025-04-22

### Fixed

-   `Text` components now correctly handle keyword arguments. They also are able to be compared to string literals (one direction only), should be rendered better in tests.

## [1.7.2] - 2025-04-17

### Fixed

-   Div, Span, Pre, and Row components now properly handle both explicit keyword arguments and \*args

## [1.7.1] - 2025-02-20

### Fixed

-   Temporarily disabled the gzip/base64 aspects of theme loading, for Skulpt compatibility

## [1.7.0] - 2025-02-20

### Added

-   There are now a bunch more themes available (`sakura`, `tacit`, `XP`, and more).
-   The deployment URLs for Skulpt and its associated files can now be overridden
-

### Fixed

-   Deployed sites were not correctly escaping HTML entities for generated tests
-   Fixed an issue where the configuration parameters were not being accepted via start_server
-   Slightly better error message when the Bakery library is not found, and assert_equal is used
-   Theme architecture is more flexible and dynamically based off `libs/manifest.json`

## [1.6.2] - 2024-12-09

### Fixed

-   The options for a `SelectBox` are forced into strings, before they are escaped.

## [1.6.1] - 2024-12-08

### Fixed

-   Using utcnow() instead of now() (credit to @crsommers)
-   Refactored `Div` and `Span` slightly (credit to @crsommers)
-   Fixed issue with escaping of tags in `VisitedPage`
-   Fixed issue with dropdowns not properly escaping the option
-   Fixed issue with non-button related values being passed incorrectly

## [1.6.0] - 2024-12-02

### Added

-   Can now test deployments with the `deploy` button, which will open a new tab with the deployed site using Skulpt
-   Configuration information is now shown on the debug page at the bottom, along with the deploy button.
-   Components that have names will now validate the name to ensure it is a valid Python variable name, and show an error.
-   Slightly more information is shown on the error page when parameter conversion fails.

### Fixed

-   MatPlotLibPlot now has correct fields
-   Arguments for Buttons can now have non-html-safe characters

## [1.5.7] - 2024-11-24

### Fixed

-   Circular references in the State now throw an error, instead of just causing an infinite loop.
-   Fixed a bug with the `safe_repr` function incorrectly marking objects that show up multiple times as circular, even if they are in sibling structures.

## [1.5.6] - 2024-11-15

### Fixed

-   Fixed a few components (`MatPlotLibPlot`, `FileUpload`, and `Text`) not rendering correctly in test cases due to not being dataclasses.
-   Fixed an issue with an incorrect import (glob) appearing somehow
-   Fixed an issue where `memoryview` was being serialized in the `safe_repr` function

## [1.5.5] - 2024-11-12

### Fixed

-   Fixed an error with `Argument` values that had quotes, not being escaped properly. Thanks new unit tests!

## [1.5.4] - 2024-11-12

### Added

-   The `set_website_style` now accepts `None` in addition to `"none"` to remove the style
-   Provide `get_main_server` and `set_main_server` functions to manipulate the global server (mostly for testing purposes).

### Fixed

-   Improved documentation for styling features

## [1.5.3] - 2024-11-7

### Added

-   The `add_website_css` function now allows a single string (just the CSS) instead of the selector/CSS pair

## [1.5.2] - 2024-10-29

### Fixed

-   Force text boxes, text areas, and other input components to `str` their default value (when provided) and escape it for html

## [1.5.1] - 2024-10-29

### Fixed

-   Fixed other input components' values not being properly escaped
-   Fixed a bug with `Span` and `Div` components not properly being `repr`ed

## [1.5.0] - 2024-10-24

### Added

-   Provide `Picture` class to prevent name collisions with `Image` class and `Pillow` module
-   Provide `new` and `open` methods in `Image` that shadow the `Pillow` module's versions.
-   Provide `UploadedFile` class to represent uploaded files in unit tests and the State.

### Fixed

-   Fixed a bug with `Button`s not properly escaping data (including unicode emojis).

## [1.4.2] - 2024-10-15

### Fixed

-   Added a `hacks.py` module to make the `MatPlotLibPlot` component work in Skulpt

## [1.4.1] - 2024-10-10

### Added

-   Improved output for very long strings of text, allowing them to be collapsed

## [1.4.0] - 2024-09-14

### Added

-   Added a "reset" button in the topright corner to reset the state and clear out the old history
-   Can now have Pillow images in State
-   Proper file handling support; this changes buttons to now POST requests instead
-   Added `Row` component, `Pre`/`PreformattedText` components

### Fixed

-   When outputing the current state, properly escape angle brackets
-   You can now add styles and attributes to `Div` and `Span` components

## [1.3.1] - 2024-08-05

### Added

-   The `Image` component now supports PIL images
-   The `Download` component also supports PIL images being provided as the `contents`

### Fixed

-   Now passing Mypy checks (although we had to silence Bakery and Bottle)

## [1.3.0] - 2024-08-05

### Added

-   New `Download` component to allow for downloading user generated files.

## [1.2.2] - 2024-07-27

### Added

-   Declared the package as providing types

## [1.2.1] - 2024-07-14

### Added

-   Added a `MatPlotLibPlot` component to display MatPlotLib plots in the browser

## [1.2.0] - 2024-05-05

### Fixed

-   Images can now deploy correctly through the CDN

## [1.1.4] - 2024-05-03

### Fixed

-   Made error lines much more intelligent

## [1.1.3] - 2024-05-03

### Fixed

-   Corrected error line stack trace depth

## [1.1.2] - 2024-05-03

### Added

-   You can now run a drafter site from the command line without starting the server (e.g., for just the tests) by setting the DRAFTER_SKIP environment variable

## [1.1.0] - 2024-04-26

### Fixed

-   The library has been broken up into multiple files for easier maintenance
-   Fixed a bug with `Argument` not handling spaces correctly, or other non-String types

### Added

-   Improved deployment options, including optional styles and header
-   Allowed frame and title to be configurable
-   Create DRAFTER_SKULPT os environment variable

## [1.0.6] - 2024-04-04

### Fixed

-   Added copyable button to the combined tests, prevent them from spilling over

## [1.0.5] - 2024-04-01

### Fixed

-   Fixed Argument instances with spaces
-   Changed button label separator to be more unusual
-   Fixed bug with additional Arguments being kept for all buttons

### Added

-   Span component to allow for a row of things

## [1.0.4] - 2024-03-30

### Fixed

-   Added button to copy all (unique) tests at once

### Removed

-   Broke external URLs, will fix in future release!

## [1.0.3] - 2024-03-29

### Fixed

-   Local images should now render correctly
-   Route tests now show the correct parameter order based on the function call they map to

## [1.0.2] - 2024-03-26

### Fixed

-   Fixed emojis not rendering correctly in the history

## [1.0.0] - 2024-03-26

### Added

-   Tests are now displayed graphically in the debug information
-   Page history is now shown as test cases, can easily copy them to clipboard
-   Improved error messages for incorrect types in page content
-   Buttons can now take Arguments, and Arguments can be embedded as hidden inputs.

## [0.2.0] - 2023-09-22

### Added

-   Current route is displayed in debug information
-   Converted parameters are now revealed in current state
-   Allow `classes` keyword parameter
-   Provide basic styling functions like `float_right` and `bold`

### Fixed

-   Reordered the debug information to put current info at top
-   Error pages now give a little more information

## [0.1.4] - 2023-09-15

### Added

-   Show produced Python pprint of Page in the Debug Information
-   Finish quickstart, rough outline of student docs
-   Show Header on top of "window" of website

## [0.1.3] - 2023-09-13

### Fixed

-   Feels weird to call it fixed, but the message now says "Drafter server starting up"
-   Allow an empty `start_server` with no routes

### Added

-   Improve PageContent classes to support keyword parameters like `style_*` to change style

## [0.1.2] - 2023-09-12

### Fixed

-   SelectBox now has a new line afterwards
-   Fixed support for list state

### Added

-   hide_debug_information() and show_debug_information() to control the debug information (defaults to visible)

## [0.1.1] - 2023-09-12

### Fixed

-   Fix support for primitive state

## [0.1.0] - 2023-09-12

### Added

-   New components: TextBox, SelectBox, CheckBox, TextArea
-   Debug data at bottom of page
-   Ability to restore state from links

## [0.0.2] - 2023-08-30

### Fixed

-   Restructured the entire project as a Git org and repo, uploaded to Pypi

## [0.0.1] - 2023-08-24

### Added

-   Initial version with Bottle support, basic link and image components, and routing

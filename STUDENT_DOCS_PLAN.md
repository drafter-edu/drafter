# Student Documentation Rewrite Plan

Status: DRAFT for stakeholder review
Date: 2026-07-26
Scope: complete rewrite of the student-facing documentation site for Drafter v2 (branch `v2-pyodide`), plus the teacher and developer areas, the examples playground, the project gallery, and a custom docs theme.

---

## 1. Executive summary

Drafter v2 ships with roughly 50 documentation pages that grew organically from the v1 site. The strongest material (the counter quickstart, the testing guide, the 21 v2-template component pages) is v2-accurate and partially runnable; the rest is a mix of v1-era prose dumps, stale navigation, dead links, and a deployment guide that students report as overwhelming. Meanwhile the package's public API has grown to 174 exported names, of which the docs cover well under half: the entire web-audio family, timers, camera, map, geolocation, media components, date/time inputs, semantic layout, and the `Fragment`/`Update`/`Redirect` payloads are effectively undocumented.

This plan replaces the current site with an intention-organized architecture (Start / Learn / Build / Examples / Reference / Help / Teach / Extend / Developers), a four-level difficulty model (First steps, Core, Advanced, Specialized), a component reference with one page per component, an interactive playground built on the existing `python drafter` runnable-fence plugin, a compiled project gallery, and a light "blueprint" visual theme with distinct darker schemes for the Teach and Developer areas.

Key facts that shape the plan:

- The hard infrastructure already exists. The MkDocs `drafter-codeblocks` plugin compiles ```` ```python drafter ```` fences into sandboxed iframes, shares one Pyodide runtime across all demos on a page (`--shared-runtime`), and already supports editable embeds. The playground is therefore a curation-and-content project, not an engineering project.
- The project gallery is the one genuinely new build: per-app compilation exists, but there is no gallery index, catalog metadata, or build pipeline.
- The existing nav is broken: `mkdocs.yml` points at a `ComponentDocs/**` tree that does not exist, while real pages (`docs/reference/*`, workbook parts 1-4) are missing from the nav. All four workbook starter-file links point at the deleted `docsrc/` tree. A rewrite is cheaper than repair.
- Coverage tooling (`tools/doc_audit.py`) and a documented plan for docstring coverage (`DOCUMENTATION_PLAN.md`) already exist and can be extended into the docs-coverage CI gates this plan requires.

Estimated shape of the finished site: ~170 pages (about 100 student-facing content pages, 57 component-reference pages, 12 teacher pages, 8 extend pages, 6 developer pages), with every canonical example executed in CI.

### Provenance legend (used throughout)

- **[R]** repository finding (verified in code or docs on `v2-pyodide`)
- **[I]** inferred requirement (derived from the project brief)
- **[REC]** recommendation (this plan's proposal; open to change)
- **[A]** assumption (believed true, not verified)
- **[Q]** unresolved question (needs stakeholder or technical resolution)

---

## 2. Audience profile [I]

Primary audience: students in a first "introduction to computer science" course taught in Python, mostly non-computing engineering majors taking their only CS course. They meet Drafter about one-third of the way through the semester and use it seriously in the final third, ending with a final project that is a Drafter application solving a problem of their choice.

What they know (shakily): functions, dataclasses, lists, `for` loops, nested data.
What they do not know and the docs must not require: exceptions, dictionaries, unstructured `break`, lambdas, list comprehensions, decorators-as-a-concept (they can use `@route` as an idiom), classes beyond dataclasses, HTML/CSS/JS (until taught in the styling section), git (until the deployment guide teaches the minimum).

Consequences for every page:

- Example code uses only the known-constructs list. Where an API tempts a forbidden construct (e.g. `dict` state, comprehensions in examples), the example uses lists of dataclasses and plain loops instead.
- `@route` and `@dataclass` are taught as "marks this function/class for Drafter", not as decorators.
- Error-handling guidance never asks students to write `try`/`except`; Drafter's own friendly error system carries that load.
- Secondary audiences (teachers, developers) get their own visually distinct areas and are never mixed into student pages.

## 3. Design principles

1. **Organize by intention, not by module.** [I] Every top-level section answers a learner question: "How do I start?", "How does this work?", "How do I do X?", "Show me one working", "What are the exact parameters?", "Why is it broken?".
2. **Four levels, one home per concept.** [I] Every piece of content is classified by the earliest point a learner needs it to complete a realistic task safely and correctly: L1 First steps (the first short tutorial: routes, pages, `start_server`, state, debug panel), L2 Core (essential for any application: core components, forms, testing, styling basics, deployment), L3 Advanced (useful for many applications: layout, tables, images, files, select/radio, fragments, custom CSS), L4 Specialized (narrow: camera, map, audio, timers, matplotlib, custom JS). The primary explanation lives at its level; deeper treatments are linked, never duplicated.
3. **Examples are the primary objects.** [I] Every concept page and how-to embeds at least one smallest-meaningful-complete runnable example (```` ```python drafter ```` fence). Examples are copyable as-is with no implied code, colocate code + output + annotation, explain cause and effect, and name safe change points and likely errors. Pages progress inspect → run → predict → modify → complete → combine → create, fading scaffolding as levels rise.
4. **A simple but correct runtime model, early.** [I][R] Students learn on day one that their program runs twice (once on their computer to start things up and run tests, once inside the browser where the real app lives), that there is no backend server, that state lives in memory and is lost on reload, and that nothing in a Drafter app is a security boundary. Incidental implementation detail (bridge, payload envelopes, Pyodide internals) is hidden; behavior affecting correctness, persistence, networking, or security never is.
5. **Types of documentation stay visibly distinct.** [I] Tutorials, concepts, how-tos, examples, and reference each use a distinct template with a page-type badge, and cross-link according to the learner's likely next question (how-to → reference for parameters; reference → concept for "why"; error entry → concept for "what did I misunderstand").
6. **Honest about security and persistence.** [I][R] No page implies that client-side validation, hidden source, browser storage, or a simulated login protects anything. The login example carries this disclaimer today [R]; the rewrite systematizes it.
7. **Accessible by default.** [I] WCAG 2.2 AA is a release requirement for the site shell, the embedded editors and demos, and the content (alt text, contrast, keyboard operation, reduced motion, no color-only meaning).
8. **Docs are versioned, tested software.** [I] Every canonical example executes in CI; coverage of `__all__` is machine-checked; template completeness is machine-checked; links and accessibility are checked on every build.
9. **Calm, professional, friendly tone.** [I] Plain language, stable technical vocabulary with plain-language glosses, no "easy/obvious/just", no em dashes, minimal emoji, no unnecessary repetition within a page.
10. **Example code is model code.** [I] Names are accurate, clear, concise, and PEP 8-conventional; functions have one responsibility; helper functions are used where they clarify; tests use Drafter's assertions (`assert_state`, `assert_content`, `assert_has`, `assert_in`) and avoid brittle whole-page snapshots unless the point is regression testing.

---

## 4. Information architecture and proposed sitemap

Top-level sections (persistent top navigation, in this order):

```
/                 Home            orientation only, three clear next steps
/start/           Start           install, first app, first look at the debugger
/learn/           Learn           concepts, guided tutorials, glossary
/build/           Build           task-oriented how-tos (styling, testing, deploying...)
/examples/        Examples        worked examples, interactive playground, project gallery
/reference/       Reference       components, functions, themes, colors, fonts
/help/            Help            error index, troubleshooting, debugging, FAQ
/teach/           Teach           instructor area (distinct dark scheme)
/extend/          Extend          Pyodide, JS interop, packages, performance, security
/dev/             Developers      architecture + full API (separate, distinct scheme)
```

[REC] Students see Start/Learn/Build/Examples/Reference/Help prominently. Teach, Extend, and Developers are collapsed into an "More" or footer-level entry on student pages, and Teach/Dev pages carry a colored banner ("Instructor documentation" / "Developer documentation — students: you probably want the Reference") with a one-click path back.

### Full sitemap

```
/
├── start/
│   ├── index                    Start here (choose your path; fast track for experienced)
│   ├── install/                 Install Drafter (Thonny, pip, command line, venv)
│   ├── first-app/               Your first website (L1 tutorial: routes, Page, state, Button)
│   ├── debug-panel/             See inside your app (L1: debug panel, tests, console)
│   └── next-steps/              Where to go next (map into Learn/Build/Examples)
├── learn/
│   ├── index
│   ├── how-drafter-works/       Runtime model: runs twice, lives in the browser, no backend
│   ├── routes-and-pages/        Routes, Page, navigation, the index route
│   ├── state/                   State: dataclasses, mutation, history, the back button
│   ├── forms-and-input/         How form fields become route parameters; type conversion
│   ├── dynamic-pages/           Conditionals, parameterized routes, Arguments
│   ├── live-updates/            Events, Fragment, Update, Redirect (concept)
│   ├── how-the-web-works/       URLs, browsers, clients and servers (general web literacy)
│   ├── software-design/         Planning an app: sketching pages, designing state, decomposition
│   ├── glossary/
│   └── tutorials/
│       ├── index                The workbook: four guided builds
│       ├── cookie-clicker/      Part 1 (retained, links fixed)
│       ├── bank-account/        Part 2
│       ├── adventure-game/      Part 3
│       └── store/               Part 4 (testing-focused)
├── build/
│   ├── index                    Task index ("I want to...")
│   ├── multiple-pages/          Linking pages together, navigation patterns
│   ├── collect-input/           Forms: text, checkboxes, dropdowns, submitting
│   ├── show-data/               Displaying lists and tables from state
│   ├── images/                  Showing and editing images (Picture, Image, uploads)
│   ├── files/                   Uploads, downloads, reading data files with open()
│   ├── styling/
│   │   ├── index                Making it look good: the three approaches, quick wins
│   │   ├── themes/              Picking and applying a theme
│   │   ├── helpers/             Styling functions and style_ keywords
│   │   ├── design-basics/       Spacing, color, typography, box model (visual design 101)
│   │   ├── custom-css/          classes, add_website_css, selectors, style tags
│   │   └── gotchas/             Weird parts: body vs the app container, theme overrides, frame
│   ├── testing/                 Testing your app with assert_ functions
│   ├── regression-tests/        Freezing pages: auto-generated tests from the debugger
│   ├── printing-and-console/    print(), console modes, the REPL
│   ├── live-updates/            Recipes: on_change, Fragment targets, Update
│   ├── timers-and-time/         Countdown, game ticks, clocks (recipes)
│   ├── html/                    Embedding raw HTML safely
│   ├── final-project/           Planning and building a complete project
│   └── deploy/
│       ├── index                What deploying means for a Drafter app (short)
│       ├── prepare/             Production prep: site info, hiding the debugger, titles
│       ├── github-pages/        Step-by-step GitHub Pages deployment (streamlined)
│       ├── troubleshooting/     Deploy failures, the dashboard, Actions logs
│       └── course-checklist/    [Q] course-specific submission steps (video, Canvas)
├── examples/
│   ├── index                    Browse by goal, concept, or component (tag index)
│   ├── calculator/  ring/  login/  forms/  pet-registry/  todo-list/  shop/  photo-editor/
│   ├── playground/
│   │   ├── index
│   │   ├── basics/  forms/  lists-and-tables/  styling/  media/  interactive/  sensors/
│   └── gallery/
│       ├── index                Full projects: try them live, read the code, remix
│       └── <project pages>      6 seed entries, each launching a compiled standalone app
├── reference/
│   ├── index
│   ├── components/              Master component list, grouped + tagged (the coherent map)
│   │   └── <57 pages, one per component or tight family — see inventory>
│   ├── page/  fragment/  update/  redirect/      Payload types
│   ├── route/  start-server/                     Core functions
│   ├── site-config/             set_website_*, add_website_*, set_site_information...
│   ├── styling-functions/       All 20 helpers + update_style/update_attr
│   ├── testing-functions/       All assert_* + set_assertion_defaults
│   ├── keyword-attributes/      style_*, classes, id, on_* events, HTML attributes
│   ├── data-types/              Picture, Photo, Location, map types, file types, audio types
│   ├── themes/                  Theme catalog with live previews/screenshots (20 themes)
│   ├── colors/  fonts/          Retained lookup tables
│   └── cli/                     Student-relevant command-line flags
├── help/
│   ├── index                    Getting help; the bug report button; asking good questions
│   ├── troubleshooting/         Symptom-based: blank page, button does nothing, no reload
│   ├── errors/
│   │   ├── index                Searchable error index (by exact error text)
│   │   └── <16+ seeded entries, one per error family>
│   ├── debug-panel/             Deep guide to all five debugger tabs
│   ├── bug-reports/             What belongs in a bug report; what is a homework question
│   └── faq/
├── teach/                       (dark scheme, "Instructor documentation" banner)
│   ├── index
│   ├── why-drafter/             Rationale and tradeoffs vs Flask/Streamlit/etc.
│   ├── big-ideas/               The concepts that matter most, in teaching order
│   ├── beyond-the-basics/       Advanced features not obvious from student docs
│   ├── lesson-plans/            index + 3 seed plans
│   ├── project-ideas/
│   ├── student-misconceptions/
│   ├── expert-misconceptions/   What Python/web devs and teachers get wrong about Drafter
│   └── classroom/               Rubrics, contingencies, offline/CDN failure plans
├── extend/
│   ├── index
│   ├── pyodide/                 How Python runs in the browser; the js module; limits
│   ├── javascript/              JS interop and custom elements
│   ├── custom-components/       Building your own components (composition → custom JS)
│   ├── packages/                Third-party libraries: matplotlib, pandas, requests, limits
│   ├── performance/
│   ├── security/                What Drafter does and does not protect; honest threat model
│   └── flask/                   Moving from Drafter to Flask (retained)
└── dev/                         (separate distinct scheme, "Developer documentation" banner)
    ├── index
    ├── architecture/            From ARCHITECTURE.md
    ├── api/                     Full generated API reference (mkdocstrings, --api builds)
    ├── contributing/            Dev setup, tests, JS watchers (from README)
    ├── docs-guide/              How to write and test documentation pages (templates, CI)
    └── internals-map/           Where things live: bridge, client server, router, payloads
```

URL conventions: [REC] directory-style URLs (`/build/styling/themes/`), lowercase-hyphenated slugs, component pages at `/reference/components/<group>/<slug>/`. Old URLs get redirects (see §8 migration map; requires adding a redirects plugin [Q — capability not currently in the repo]).

---

## 5. Page inventory

Legend for the tables below.
Audience: **S** students, **T** teachers, **D** developers. Type: **Idx** index/landing, **Tut** tutorial, **Con** concept, **How** how-to, **Ex** worked example, **Play** playground collection, **Gal** gallery entry, **CompRef** component reference, **Ref** other reference, **Trb** troubleshooting, **Les** lesson plan, **Mis** misconception entry. Level: **L1** First steps, **L2** Core, **L3** Advanced, **L4** Specialized, **—** unleveled. Priority: **P0** minimum viable student pathway, **P1** first full release, **P2** post-release. Status: retain / revise / split / merge / create / remove (relative to existing content named in Source).
Abbreviations: **CRT** = full component reference template (§7.4); **TRB7** = 7-part troubleshooting structure (§7.7); **nR** = n runnable `python drafter` demos.

### 5.1 Home and Start

| Proposed URL | Page title | Aud | Type | Level | Learner goal | Prerequisites | Required content | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/` | Drafter | S | Idx | — | Understand what Drafter is; pick the right next step | none | One-paragraph pitch; three cards (Start the tutorial / Browse examples / Find a component); quiet links to Teach and Dev; no walls of links | 1R hero counter (optional) | start/first-app, examples, reference/components | docs/index.md | P0 | revise (rewrite) |
| `/start/` | Start here | S | Idx | L1 | Choose install path and entry point; fast track for experienced coders | none | Two paths (new vs experienced); prerequisite check ("you should know functions, dataclasses, lists"); time estimates | 0 | install, first-app | new | P0 | create |
| `/start/install/` | Install Drafter | S | How | L1 | Get Drafter running locally | Python installed | Thonny package manager path; pip path; verify with one command; common install failures; editor-agnostic note | 0 | first-app, help/troubleshooting | students/installation.md | P0 | revise |
| `/start/first-app/` | Your first website | S | Tut | L1 | Build and run a working counter site in ~20 minutes | install | `start_server`, `@route`, `Page`, string content, dataclass state, `Button`; predict-and-modify prompts; expected result stated; likely first errors | 7R | debug-panel, learn/how-drafter-works, learn/routes-and-pages | quick/quickstart.md | P0 | revise (expand) |
| `/start/debug-panel/` | See inside your app | S | Tut | L1 | Read state, history, and test results in the debugger | first-app | Frame tour; Current tab (state viewer); History tab; where tests appear; where print() goes; how errors display; what "no debug panel" (production) means | 2R | help/debug-panel, build/testing | new; js/src/debug/index.tsx [R] | P0 | create |
| `/start/next-steps/` | Where to go next | S | Idx | L1 | Pick the next thing to learn after the first app | first-app | Map: concepts → Learn; tasks → Build; browse → Examples; component lookup → Reference; final-project pointer | 0 | learn, build, examples | new | P1 | create |

### 5.2 Learn

| Proposed URL | Page title | Aud | Type | Level | Learner goal | Prerequisites | Required content | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/learn/` | Learn | S | Idx | — | Find the right concept page or tutorial | none | Concept list with one-line summaries; tutorials strip; glossary link | 0 | all learn pages | new | P0 | create |
| `/learn/how-drafter-works/` | How Drafter works | S | Con | L1 | Hold a correct minimal runtime model | first-app | Runs twice (your computer: tests + startup; browser: the real app); no backend server; state in memory, lost on reload; what `persistent=True` means (pointer); nothing here is secret or secure; diagram | 1R | learn/state, extend/pyodide, extend/security | ARCHITECTURE.md (condensed) | P0 | create |
| `/learn/routes-and-pages/` | Routes and pages | S | Con | L2 | Explain what a route is and how pages connect | first-app | `@route` as "makes this function a page"; the `index` route; route names as URLs; returning `Page`; linking via Button/Link; route verification errors | 3R | reference/route, reference/page, build/multiple-pages | quick/quickstart.md, students/docs.md | P0 | create |
| `/learn/state/` | State | S | Con | L2 | Design and reason about application state | first-app, dataclasses | State as one dataclass; passing state to routes; mutating fields; state flows route → page → next route; history and back button; what resets on reload; allowed field types; nested dataclasses and lists | 3R | learn/how-drafter-works, examples/pet-registry, help/errors (state mismatch) | quick/quickstart.md, ARCHITECTURE.md | P0 | create |
| `/learn/forms-and-input/` | Forms and input | S | Con | L2 | Explain how a form field's value reaches a route function | routes-and-pages, state | The name→parameter contract; submit via Button; type conversion table (str/int/float/bool); defaults; what happens on conversion failure (friendly error) | 3R | build/collect-input, reference/components (forms group), help/errors | students/docs.md; router/parameters [R] | P0 | create |
| `/learn/dynamic-pages/` | Dynamic pages | S | Con | L3 | Make one route render differently based on state and arguments | forms-and-input | Conditionals in routes; helper functions returning components; `Argument` for per-button data; reusing routes; list-driven rendering | 3R | reference/components/argument, examples/shop | button_arguments.py, shop.py [R] | P1 | create |
| `/learn/live-updates/` | Live updates | S | Con | L3 | Understand events and partial updates | dynamic-pages | `on_change`/`on_input` etc. as "call a route when..."; `Fragment` replaces part of a page; `Update` changes state silently; `Redirect`; when to prefer full pages | 3R | build/live-updates, reference/fragment, reference/update | payload_types.py, event_handlers_demo.py [R] | P1 | create |
| `/learn/how-the-web-works/` | How the web works | S | Con | L2 | Basic web literacy: URLs, browsers, servers | none | URL anatomy; browser fetches and renders; client vs server in general; where Drafter fits (front-end only); why localhost URLs die with your program | 0 | learn/how-drafter-works, build/deploy | new; deployment.md warning box | P1 | create |
| `/learn/software-design/` | Designing your app | S | Con | L3 | Plan an application before coding | state, routes-and-pages | Sketch pages first; route map diagrams (mermaid); design state from the sketches; one-responsibility route functions; helper decomposition; iterate small | 1R | build/final-project, teach/project-ideas | workbook mermaid diagrams [R] | P1 | create |
| `/learn/glossary/` | Glossary | S | Ref | — | Look up terms | none | Stable vocabulary with plain-language pairs: route, state, component, page, server, render, deploy, fragment, regression test, theme... each linking to its concept page | 0 | all | new | P1 | create |
| `/learn/tutorials/` | The workbook | S | Idx | — | Choose a guided build | first-app | Four tutorials with teaches/requires table; expected time; starter files hosted in docs assets (fix dead `docsrc/` links [R]) | 0 | four tutorial pages | workbook/index.md | P1 | revise |
| `/learn/tutorials/cookie-clicker/` | Cookie Clicker | S | Tut | L2 | Build a click counter with tests | first-app | Retain structure; fix starter link; remove stale "Bottle backend" output [R]; runnable final version | 2R | tutorials/bank-account | workbook/part1/cookie.md | P1 | revise |
| `/learn/tutorials/bank-account/` | Bank account | S | Tut | L2 | Multi-route app with form input | cookie-clicker | Retain spec; fix starter link; runnable final version; route diagram | 2R | build/collect-input | workbook/part2/bank.md | P1 | revise |
| `/learn/tutorials/adventure-game/` | Adventure game | S | Tut | L2 | Branching pages, conditional content, images | bank-account | Retain spec; fix starter and image links; runnable final version | 2R | learn/dynamic-pages, examples/gallery | workbook/part3/adventure.md | P1 | revise |
| `/learn/tutorials/store/` | Store: testing practice | S | Tut | L2 | Generate regression tests from a finished app | adventure-game, build/testing | Retain concept; fix starter link; align with v2 debugger UI names | 1R | build/regression-tests | workbook/part4/store.md | P1 | revise |

### 5.3 Build

| Proposed URL | Page title | Aud | Type | Level | Learner goal | Prerequisites | Required content | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/build/` | Build | S | Idx | — | Find the how-to for a task | none | "I want to..." task index grouped by goal; level badges | 0 | all build pages | new | P0 | create |
| `/build/multiple-pages/` | Add more pages | S | How | L2 | Create and link several pages | first-app | New routes; Button vs Link; shared header helper function; go-back patterns; route-not-found error pointer | 2R | learn/routes-and-pages, examples/ring | simple_ring.py, examples/ring.md | P0 | create |
| `/build/collect-input/` | Collect input with forms | S | How | L2 | Build working forms | learn/forms-and-input | TextBox/TextArea/CheckBox/SelectBox recipes; labeling; defaults; multi-field form → multi-parameter route; testing a form route | 4R | component pages (forms group), examples/forms | examples/forms.md, complex_form.py | P0 | create |
| `/build/show-data/` | Show lists and tables | S | How | L2 | Display collections from state | learn/state | BulletedList/NumberedList from a list; Table from list of dataclasses; building rows with a loop + helper; empty-state handling | 3R | component pages (lists, table), examples/todo-list | table.py, todo_list.py, examples/nested_data.md | P0 | create |
| `/build/images/` | Work with images | S | How | L3 | Show, upload, and edit images | collect-input | Image from URL/file; Picture type; upload via FileUpload with Picture parameter; transforms; download results; deploy note (bundle image files) | 4R | reference/data-types/picture, components camera/image | students/pictures.md, picture_upload.py | P1 | revise (from pictures.md) |
| `/build/files/` | Upload, download, and read files | S | How | L3 | Move files in and out of the app | collect-input | FileUpload parameter types (str/bytes/file types); Download; reading bundled data files with `open()`; what the browser allows; deploy `--additional-paths` pointer | 3R | components fileupload/download, reference/cli | file_upload.py, download_result.py, files/opening [R] | P1 | create |
| `/build/styling/` | Make it look good | S | How | L2 | Choose a styling approach; get quick wins | first-app | The three tiers (themes → helpers/keywords → CSS) and when each is enough; one worked restyle of a plain page; pointers to subpages | 2R | styling subpages, reference/themes | students/styling.md | P0 | split (from styling.md) |
| `/build/styling/themes/` | Use a theme | S | How | L2 | Restyle the whole site in one line | styling | `set_website_style` / `start_server(theme=...)`; the 20-theme catalog with thumbnails; live switcher in debugger; `none` for full control; did-you-mean errors | 2R | reference/themes | students/styling.md, styling/themes.py [R] | P0 | split |
| `/build/styling/helpers/` | Styling functions and keywords | S | How | L2 | Style individual components without CSS | styling | Helper functions by intent (emphasis, color, size, position, spacing); `style_*` keywords and the underscore→hyphen rule; combining; testing styles with assert_style | 3R | reference/styling-functions, build/testing | students/styling.md | P0 | split |
| `/build/styling/design-basics/` | Design basics | S | Con | L2 | Apply spacing, color, and typography deliberately | styling/helpers | White space and alignment; color: contrast, palettes, meaning never by color alone; typography: sizes, hierarchy, line length; the CSS box model (margin/border/padding) mapped to `change_margin`/`change_border`/`change_padding`; external deep links (MDN, web.dev) | 3R | styling/custom-css, reference/colors, reference/fonts | new [I] | P1 | create |
| `/build/styling/custom-css/` | Custom CSS | S | How | L3 | Use real CSS with classes | design-basics | `classes` keyword; `add_website_css` (both forms); selectors 101; style tags in pages; specificity vs themes; box model applied | 3R | styling/gotchas, external CSS tutorials | students/styling.md | P1 | split |
| `/build/styling/gotchas/` | Styling gotchas | S | Trb | L3 | Avoid the weird parts of styling a Drafter page | custom-css | Styling `body` also styles the debug panel — target Drafter's app container class instead [Q: verify exact selector]; theme specificity overriding your CSS (`none` escape); the window frame and `set_website_framed`; full-width layouts; shadow DOM option; styles invisible to assert_style | 3R | help/errors, reference/site-config | new [I]; js/src/css [R] | P1 | create |
| `/build/testing/` | Test your app | S | How | L2 | Write focused tests for routes | learn/forms-and-input | Retain current guide: routes are callable; assert_ family table; loose-by-default matching; flags; set_assertion_defaults; tests in the debug panel | 3R | reference/testing-functions, build/regression-tests | students/testing.md | P0 | revise (light) |
| `/build/regression-tests/` | Freeze finished pages | S | How | L3 | Auto-generate regression tests | build/testing | Page Load History → copy as test; when to freeze; updating stale frozen tests; circular-reference gotcha pointer | 1R | help/errors/circular-reference, start/debug-panel | students/testing.md (§auto), students/help.md | P1 | split |
| `/build/printing-and-console/` | Print and the console | S | How | L2 | Use print() to see what's happening | first-app | Where print output goes; the four console modes; the REPL shares your variables; production behavior | 2R | start/debug-panel | students/console.md | P1 | revise |
| `/build/live-updates/` | Update part of a page | S | How | L3 | React to input without a full page change | learn/live-updates | Recipe: live character counter (on_input + Fragment); recipe: silent state save (Update); recipe: redirect after submit; targeting by id/class | 3R | reference/fragment, reference/update, reference/redirect | payload_types.py, event_handlers_demo.py | P1 | create |
| `/build/timers-and-time/` | Timers and clocks | S | How | L4 | Make things happen over time | live-updates | Countdown quiz timer; game tick with Clock; pausing/controls; persistent timers across pages; date/time inputs pointer | 2R | components timer/clock, examples/playground/interactive | timer_example.py | P2 | create |
| `/build/html/` | Embed HTML | S | How | L3 | Use raw HTML when components aren't enough | styling/custom-css | Strings can hold HTML; RawHTML; escaping and safety (never render user input as HTML); when a component exists, prefer it | 2R | reference/components/rawhtml | students/html.md | P2 | revise |
| `/build/final-project/` | Build a complete project | S | How | L2 | Scope, plan, and finish a project app | learn/software-design | Scope advice (2-5 pages, one clear job); plan → state → routes → pages workflow; milestone checklist; testing as you go; styling last; deploy pointer; gallery for inspiration | 1R | examples/gallery, build/deploy | new [I]; deployment.md fragments | P1 | create |
| `/build/deploy/` | Deploy your site | S | How | L2 | Understand what deployment is; see the 3 steps | first-app | What compiling to a static site means (still no backend); the three-step overview (prepare → upload → deploy); expected result; time estimate | 0 | deploy subpages | students/deployment.md | P0 | split (rewrite) |
| `/build/deploy/prepare/` | Prepare for release | S | How | L2 | Make the app production-ready | deploy | `set_site_information`; `hide_debug_information`; `set_website_title`; `set_website_framed(False)`; optional custom error page; the `--about` page; test locally first | 2R | reference/site-config, deployed_full_width.py | students/deployment.md | P0 | split |
| `/build/deploy/github-pages/` | Publish on GitHub Pages | S | How | L2 | Get the site live | prepare | Streamlined numbered steps with progressive disclosure (details boxes for screenshots); enable Pages; add files; run the workflow; find your URL; verify from another device | 0 | deploy/troubleshooting | students/deployment.md | P0 | split (streamline) |
| `/build/deploy/troubleshooting/` | Fix a failed deployment | S | Trb | L2 | Diagnose and retry failed deploys | github-pages | Reading Actions logs (red X path); the deployment dashboard; TRB7-style top failures (Pages not enabled, syntax error, missing file, wrong filename); re-running the workflow | 0 | help/errors | students/deployment.md | P0 | split |
| `/build/deploy/course-checklist/` | Course submission checklist | S | How | — | Complete course-specific submission steps | github-pages | [Q — stakeholder decision] Video recording guidance, planning document upload, Canvas submission, instructor-URL setup; clearly marked as course-specific and separable | 0 | deploy pages | students/deployment.md | P1 | split (decision needed) |

### 5.4 Examples

| Proposed URL | Page title | Aud | Type | Level | Learner goal | Prerequisites | Required content | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/examples/` | Examples | S | Idx | — | Find an example by goal, concept, or component | none | Tag-indexed browser (goal, API symbol, concept, difficulty, runtime needs); worked examples strip; playground and gallery entries | 0 | all example pages | examples/examples.md | P0 | revise (rebuild) |
| `/examples/calculator/` | Calculator | S | Ex | L2 | Forms + state in one small app | first-app | Inspect→run→predict→modify→remix structure; tests included; safe change points; likely errors | 2R | build/collect-input | examples/calculator.md, calculator.py | P0 | revise |
| `/examples/ring/` | Three linked pages | S | Ex | L2 | Multi-page navigation, stateless | first-app | Same structure; Link usage; consistent `@route` style (fix mixed forms [R]) | 1R | build/multiple-pages | examples/ring.md, simple_ring.py | P0 | revise |
| `/examples/forms/` | Big form | S | Ex | L2 | Every core input in one form | collect-input | Make runnable (currently static [R]); add missing dataclass import [R]; tests | 1R | build/collect-input | examples/forms.md | P0 | revise |
| `/examples/login/` | Login flow | S | Ex | L3 | Conditional pages from state | dynamic-pages | Make runnable; keep and strengthen the "this is not security" disclaimer; tests | 1R | extend/security, learn/dynamic-pages | examples/login.md, simple_login.py | P1 | revise |
| `/examples/pet-registry/` | Pet registry | S | Ex | L3 | Nested data: list of dataclasses | show-data | Rework nested_data.md: add/view records, Table rendering, runnable, tests | 1R | build/show-data | examples/nested_data.md | P1 | revise (rename) |
| `/examples/todo-list/` | To-do list | S | Ex | L2 | Add/remove items from list state | show-data | New worked example from todo_list.py; remix prompts | 1R | build/show-data | examples/todo_list.py | P1 | create |
| `/examples/shop/` | Shop | S | Ex | L3 | Arguments, inventory state, multiple routes | dynamic-pages | New worked example from shop.py; per-button Arguments; tests | 1R | learn/dynamic-pages | examples/shop.py | P1 | create |
| `/examples/photo-editor/` | Photo editor | S | Ex | L3 | Upload and transform images | build/images | From picture_upload.py (already exemplary [R]); tests | 1R | build/images | examples/picture_upload.py | P1 | create |
| `/examples/playground/` | Playground | S | Idx | — | Run and edit many small programs | first-app | What the playground is; editable embeds note; collection cards; performance note (demos share one runtime) | 0 | collections | new; mkdocs plugin [R] | P1 | create |
| `/examples/playground/basics/` | Basics | S | Play | L1 | Tinker with hello/counter/pages | first-app | 5-8 editable demos: hello, counter, two pages, initial state, emoji button; each links to its concept page | 6R | start/first-app | simplest.py, cookie_clicker.py, string_state.py | P1 | create |
| `/examples/playground/forms/` | Forms | S | Play | L2 | Tinker with every input type | collect-input | 6-10 editable demos incl. date/time inputs, RelatedCheckBox list, RadioButtonGroup | 8R | build/collect-input | all_forms.py, multi_select.py, textbox_example.py | P1 | create |
| `/examples/playground/lists-and-tables/` | Lists and tables | S | Play | L2 | Tinker with data display | show-data | 4-6 demos: lists, Table from dataclasses, DefinitionList, ProgressBar/Meter | 5R | build/show-data | table.py, todo_list.py | P1 | create |
| `/examples/playground/styling/` | Styling | S | Play | L2 | See styling approaches side by side | build/styling | 6-8 demos: theme switch, helpers, style_ keywords, classes + CSS, box model visualizer | 7R | build/styling | styling_example.py, fun_style.py, animations.py, theme_support.py | P1 | create |
| `/examples/playground/media/` | Images and media | S | Play | L3 | Tinker with images, audio, video | build/images | 5-7 demos: Image sources, Picture transforms, Download, Audio/Video, matplotlib plot | 6R | build/images, components | simple_image.py, pil_image.py, plotting.py, background_music.py | P2 | create |
| `/examples/playground/interactive/` | Interactive | S | Play | L3 | Tinker with events and partial updates | live-updates | 5-7 demos: on_input counter, Fragment target, Update, Timer, Clock, transitions | 6R | build/live-updates | event_handlers_demo.py, payload_types.py, timer_example.py, transition_example.py | P2 | create |
| `/examples/playground/sensors/` | Camera, location, sound | S | Play | L4 | Tinker with device features | components | 5-7 demos: Camera capture, CurrentLocation, Map markers, Tone/Melody, Microphone meter; permission notes | 6R | specialized component pages | camera_demo.py, geolocation_demo.py, map_example.py, audio_playground.py | P2 | create |
| `/examples/gallery/` | Project gallery | S | Idx | — | See what a finished project looks like | first-app | Cards: screenshot, one-line pitch, concepts used, Try it (opens compiled app in new tab), Read the code, Download-and-remix; "what makes this a good project" notes | 0 | build/final-project | new [I]; compile pipeline [R] | P1 | create |
| `/examples/gallery/<6 seed projects>` | (six project pages) | S | Gal | L3 | Study a complete application | varies | Per §7.8 template: live launch, annotated source, state diagram, route map, remix ideas; 6 seeds [Q: candidates below] | launch + source | related concepts | shop.py (expanded), adventure (workbook final), sophisticated_demo.py, secret_examples [Q permission], 2 new-built | P2 | create |

### 5.5 Reference — core pages

| Proposed URL | Page title | Aud | Type | Level | Learner goal | Prerequisites | Required content | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/reference/` | Reference | S | Idx | — | Find authoritative details fast | none | Section map: components master list, functions, types, themes, colors/fonts, CLI | 0 | all reference | reference/reference.md | P0 | revise |
| `/reference/components/` | All components | S | Ref | — | See every component, organized coherently | first-app | Master list grouped by purpose (12 groups, §5.6) with one-line descriptions, level badges, tags; adjacency navigation ("other input components"); search by what-you-want-to-do | 0 | every component page | reference/components.md; `__all__` [R] | P0 | merge (rebuild) |
| `/reference/page/` | Page | S | Ref | L1 | Exact Page behavior | first-app | Signature `Page(state, content)` and stateless form; content validation rules; css/js params (L4 note); link verification; unique-name rule | 2R | fragment, learn/routes-and-pages | payloads/kinds/page.py [R] | P0 | create |
| `/reference/fragment/` | Fragment | S | Ref | L3 | Partial page updates | page | Signature; target forms (id/class/attr/None); when triggered element is the target | 2R | build/live-updates | payloads [R] | P1 | create |
| `/reference/update/` | Update | S | Ref | L3 | State-only responses | fragment | Signature; no render; use cases | 1R | build/live-updates | payloads [R] | P1 | create |
| `/reference/redirect/` | Redirect | S | Ref | L3 | Navigate from a route | page | Signature; kwargs become target arguments; history behavior | 1R | build/live-updates | payloads [R]; emojis.py | P1 | create |
| `/reference/route/` | route | S | Ref | L1 | Exact route decorator behavior | first-app | `@route`, `@route("url")`, `add_route`; name→URL rule; state injection rule (first param); extra params from forms/arguments; `_`-prefixed injected params (L4) | 2R | learn/routes-and-pages | router/commands.py [R] | P0 | create |
| `/reference/start-server/` | start_server | S | Ref | L1 | Exact start_server options | first-app | Student-relevant params (initial_state, theme, site_title, framed, in_debug_mode, port, engine...); precedence note; deprecated v1 params warn-and-ignore [R] | 1R | reference/site-config, reference/cli | launch.py [R], README | P0 | create |
| `/reference/site-config/` | Site configuration functions | S | Ref | L2 | Look up every set_/add_ helper | start-server | One entry each: set_website_title/favicon/framed/style, set_page_transition, set_error_page, set_button_spinners, add_website_header/css, set_site_information/get_site_information, hide/show_debug_information, deploy_site; placement guidance (after imports) | per-entry 1R | build/deploy/prepare, build/styling | deploy.py [R]; README table | P0 | create |
| `/reference/styling-functions/` | Styling functions | S | Ref | L2 | Look up every styling helper | build/styling/helpers | All 20 helpers with signature, CSS effect, example; update_style/update_attr; chainability; strings and lists accepted; note change_text_transform export gap [Q] | per-entry snippets | build/styling/helpers | students/styling.md; styling/styling.py [R] | P0 | create |
| `/reference/testing-functions/` | Testing functions | S | Ref | L2 | Look up every assertion | build/testing | All 15 assert_/config functions: signature, what it checks, failure output sample, flags | per-entry snippets | build/testing | testing/asserts.py [R]; students/testing.md | P1 | create |
| `/reference/keyword-attributes/` | Keywords every component accepts | S | Ref | L3 | Understand extra_settings | components | `style_*` rule; `classes`; `id`; plain HTML attributes; `on_*` events list; `arguments`; underscore→hyphen conversion | 2R | build/styling/helpers, learn/live-updates | components/page_content.py [R] | P1 | create |
| `/reference/data-types/` | Data types | S | Idx | L3 | Find value-type docs | components | Index of Picture, Photo, Location, MapLocation/MapMarker/MapView, DrafterTextFile/DrafterBinaryFile, AudioLevel/Recording | 0 | subpages | data/ modules [R] | P1 | create |
| `/reference/data-types/picture/` | Picture | S | Ref | L3 | Full Picture API | build/images | Constructors/classmethods; transforms; pixels; to_/from_ conversions; laziness of URL pictures; equality; PIL bridge | 2R | build/images, components/image | data/images.py [R]; students/pictures.md | P1 | split (from pictures.md) |
| `/reference/data-types/photo/` | Photo | S | Ref | L4 | Camera result type | camera | Fields, statuses, `.picture` | 1R | components/camera | components/camera.py [R] | P2 | create |
| `/reference/data-types/location-types/` | Location and map types | S | Ref | L4 | Geo value types | map/geolocation | Location fields/statuses; MapLocation/MapMarker/MapView; AddMarkerFunction | 1R | components/map | components/map.py [R] | P2 | create |
| `/reference/data-types/file-types/` | File types | S | Ref | L3 | Upload result types | build/files | DrafterTextFile/DrafterBinaryFile fields; parameter-type table for FileUpload | 1R | components/fileupload | data/files.py [R] | P2 | create |
| `/reference/data-types/audio-types/` | Audio types | S | Ref | L4 | Mic/recorder result types | audio components | AudioLevel, Recording fields; playing a Recording via Sound | 1R | components (sound group) | components/audio.py [R] | P2 | create |
| `/reference/themes/` | Theme catalog | S | Ref | L2 | Preview and choose among all 20 themes | build/styling/themes | Screenshot/live preview per theme; upstream credit links; selection code; `none`; note dormant darkfairy/matcha [Q] | 1R per theme (or generated previews) | build/styling/themes | styling/themes.py, js/src/css/themes [R] | P0 | create |
| `/reference/colors/` | HTML colors | S | Ref | L2 | Look up color names | styling | Retain generated table; add contrast guidance link | 0 | design-basics | reference/colors.md | P1 | retain |
| `/reference/fonts/` | Fonts | S | Ref | L2 | Look up safe fonts | styling | Retain table; add pairing advice link | 0 | design-basics | reference/fonts.md | P1 | retain |
| `/reference/cli/` | Command line | S | Ref | L3 | Student-relevant flags | install | `drafter file.py`; `--compile`; port/host; `--production`; theme; pointer to full CLI in dev docs | 0 | build/deploy, dev docs | README CLI tables | P2 | create |

### 5.6 Reference — component pages (57 pages)

All rows share: Audience **S**; Type **CompRef**; Required content **CRT** (Name, one-line description, when-to-use, Syntax, Parameters table with types/defaults/constraints, 1-3 runnable Examples, Notes including failure modes, Related components strip, external links); Status **create** unless a Source page exists (then **revise**). Prerequisites: `/start/first-app/` plus any listed. Group pages give adjacency ("other components in this group" auto-strip).

| Proposed URL (under `/reference/components/`) | Page title | Level | Learner goal (beyond CRT) | Extra prereqs | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|
| `actions/button/` | Button | L2 | Trigger a route; pass Arguments | — | 4R | link, argument | components/basic/button.md [R] | P0 | revise |
| `actions/link/` | Link | L2 | Navigate by text link; external URLs | — | 2R | button | components/basic/link.md (fix v1 URL [R]) | P0 | revise |
| `actions/argument/` | Argument | L3 | Pass extra values to a route | forms concept | 2R | button, learn/dynamic-pages | components/basic/argument.md | P1 | revise |
| `input/textbox/` | TextBox | L2 | Collect a line of text/number | forms concept | 2R | textarea, label | components/basic/text_box.md | P0 | revise |
| `input/textarea/` | TextArea | L2 | Collect multi-line text | forms concept | 2R | textbox | components/basic/text_area.md | P0 | revise |
| `input/checkbox/` | CheckBox | L2 | Collect a yes/no | forms concept | 2R | relatedcheckbox, radiobuttongroup | components/basic/check_box.md | P0 | revise |
| `input/selectbox/` | SelectBox | L3 | Choose one from a list | forms concept | 2R | radiobuttongroup | components/advanced/select_box.md (fix "Fih" typo [R]) | P1 | revise |
| `input/radiobuttongroup/` | RadioButtonGroup | L3 | Choose one, all options visible | forms concept | 2R | selectbox | forms.py [R]; export gap [Q] | P1 | create |
| `input/relatedcheckbox/` | RelatedCheckBox | L3 | Choose many → list parameter | checkbox | 2R | checkbox | multi_select.py [R] | P1 | create |
| `input/dateinput/` | DateInput | L3 | Collect a date | forms concept | 1R | timeinput, datetimeinput | all_forms.py [R] | P1 | create |
| `input/timeinput/` | TimeInput | L3 | Collect a time | forms concept | 1R | dateinput | all_forms.py [R] | P1 | create |
| `input/datetimeinput/` | DateTimeInput | L3 | Collect date+time | forms concept | 1R | dateinput | all_forms.py [R] | P1 | create |
| `input/label/` | Label | L3 | Caption an input accessibly | any input | 2R | textbox; a11y note required | labeled_form.py [R] | P1 | create |
| `input/output/` | Output | L3 | Show a computed result region | live-updates | 1R | fragment | output.py, payload_types.py [R] | P2 | create |
| `input/fileupload/` | FileUpload | L3 | Receive a file from the user | forms concept | 2R | download, data-types/file-types | components/advanced/files/file_upload.md | P1 | revise |
| `input/download/` | Download | L3 | Let the user save a file | — | 2R | fileupload | components/advanced/files/download.md | P1 | revise |
| `text/text/` | Text | L2 | Explicit text component | — | 1R | span | text.py [R] | P1 | create |
| `text/header/` | Header | L2 | Section headings, levels 1-6 | — | 1R | learn/routes-and-pages | components/advanced/formatting/header.md | P0 | revise |
| `text/paragraph/` | Paragraph | L3 | Real paragraphs vs strings | — | 1R | text | layout.py [R] | P2 | create |
| `text/pre/` | PreformattedText | L3 | Preserve spacing/newlines | — | 1R | inlinecode | formatting/preformatted_text.md | P1 | revise |
| `text/inlinecode/` | InlineCode | L3 | Mark code in text | — | 1R | pre | text.py [R] | P2 | create |
| `text/blockquote/` | BlockQuote | L3 | Quote a passage | — | 1R | text group | text.py [R] | P2 | create |
| `text/inline-styles/` | Inline text semantics (family) | L3 | Strong, Emphasis, Mark, Kbd, Samp, Small, Sup, Sub, Var, Q, Dfn, Abbr, Del, Ins in one page with a rendered table | — | 2R | styling/helpers | text.py [R]; grouped page [REC] | P2 | create |
| `layout/div/` | Div (Box) | L3 | Group content for styling | styling | 2R | span, row | formatting/div_row.md | P1 | revise (split) |
| `layout/span/` | Span | L3 | Inline grouping | styling | 2R | div | formatting/span.md | P1 | revise |
| `layout/row/` | Row | L3 | Side-by-side layout | div | 2R | div; flexbox note | formatting/div_row.md | P1 | revise (split) |
| `layout/linebreak/` | LineBreak | L2 | Force a new line | — | 1R | horizontalrule | formatting/line_break.md | P0 | revise |
| `layout/horizontalrule/` | HorizontalRule | L2 | Divider line | — | 1R | linebreak | students/docs.md | P0 | create |
| `layout/details/` | Details | L3 | Collapsible sections, accordions | — | 1R | div | layout.py [R] | P2 | create |
| `layout/page-regions/` | Page regions (family) | L4 | Section, Article, Aside, Main, Nav, HeaderContent, FooterContent, Figure, FigureCaption in one page | div | 1R | custom-components | layout.py [R]; grouped [REC] | P2 | create |
| `lists/bulletedlist/` | BulletedList | L2 | Unordered list from a Python list | — | 1R | numberedlist, show-data | components/basic/bulleted_list.md | P0 | revise |
| `lists/numberedlist/` | NumberedList | L2 | Ordered list | — | 1R | bulletedlist | components/basic/numbered_list.md | P0 | revise |
| `lists/definitionlist/` | DefinitionList | L3 | Term/definition pairs; dataclass rendering | — | 1R | table | layout.py [R] | P2 | create |
| `data/table/` | Table | L3 | Rows of lists or dataclasses | show-data | 2R | definitionlist | components/advanced/table.md | P1 | revise |
| `data/progressbar/` | ProgressBar | L3 | Show progress | — | 1R | meter | output.py [R] | P2 | create |
| `data/meter/` | Meter | L3 | Show a gauge value | — | 1R | progressbar | output.py [R] | P2 | create |
| `data/timeoutput/` | TimeOutput | L4 | Semantic timestamps | — | 1R | data group | output.py [R] | P2 | create |
| `media/image/` | Image | L3 | Show images from URL/file/Picture/bytes | — | 2R | data-types/picture, build/images | components/advanced/image.md | P1 | revise |
| `media/audio/` | Audio | L4 | Play sound files; persistence | — | 1R | sound, timer (persistent) | background_music.py [R] | P2 | create |
| `media/video/` | Video | L4 | Play video files | — | 1R | audio | media.py [R] | P2 | create |
| `media/canvas/` | Canvas | L4 | Drawing surface (with JS) | extend/javascript | 1R | svg | media.py [R] | P2 | create |
| `media/svg/` | SVG | L4 | Inline vector graphics | — | 1R | canvas | media.py [R] | P2 | create |
| `media/matplotlibplot/` | MatPlotLibPlot | L4 | Show a matplotlib figure | matplotlib basics | 2R | extend/packages | plotting.py [R]; specialized stub [R] | P1 | create |
| `media/rawhtml/` | RawHTML and HtmlTag | L3 | Escape hatch to HTML | build/html | 1R | build/html; safety note required | text.py [R] | P2 | create |
| `time/timer/` | Timer | L4 | Countdown that fires a route | live-updates | 2R | clock | timer_example.py [R] | P1 | create |
| `time/clock/` | Clock | L4 | Repeating tick route | timer | 1R | timer | timer.py [R] | P2 | create |
| `time/removepersistent/` | RemovePersistent | L4 | Evict a persistent component | timer/audio | 1R | timer, audio | persistence.py [R] | P2 | create |
| `place/map/` | Map | L4 | Interactive map with markers | live-updates | 2R | location-types, currentlocation; network note | map_example.py [R] | P1 | create |
| `place/currentlocation/` | CurrentLocation | L4 | Ask for the user's location | forms concept | 1R | map; permission/privacy note required | geolocation_demo.py [R] | P1 | create |
| `capture/camera/` | Camera | L4 | Take a photo into the app | forms concept | 2R | data-types/photo, image; permission note | camera_demo.py [R] | P1 | create |
| `sound/tone/` | Tone | L4 | Play a single note | — | 1R | melody | audio_playground.py [R] | P2 | create |
| `sound/melody/` | Melody | L4 | Play a note sequence | tone | 1R | tone, sound | audio_playground.py [R] | P2 | create |
| `sound/sound/` | Sound | L4 | Play files through effects | — | 1R | audio, audio-types | audio.py [R] | P2 | create |
| `sound/microphone/` | Microphone | L4 | React to sound levels | live-updates | 1R | audiorecorder; permission note | audio.py [R] | P2 | create |
| `sound/audiorecorder/` | AudioRecorder | L4 | Record audio clips | microphone | 1R | sound, audio-types | audio.py [R] | P2 | create |
| `sound/effects/` | Audio effects (family) | L4 | Echo, Reverb, Muffle, Sharpen, Distortion in one page | sound | 1R | sound, tone | audio.py [R]; grouped [REC] | P2 | create |

[REC] Two deliberate deviations from "every component gets its own page": the 14 inline text semantic components and the 9 semantic page regions are grouped onto family pages (each member still gets its own anchor, syntax block, and example row), because 23 near-identical stub pages would hurt search and adjacency more than help. The 5 audio effects are grouped for the same reason. All other components get dedicated pages.

### 5.7 Help

| Proposed URL | Page title | Aud | Type | Level | Learner goal | Prerequisites | Required content | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/help/` | Help | S | Idx | — | Choose the right help path | none | Decision strip: error message → error index; wrong behavior → troubleshooting; understand the debugger → guide; Drafter bug → bug reports | 0 | all help | students/help.md | P0 | revise (rebuild) |
| `/help/troubleshooting/` | Troubleshooting | S | Trb | — | Diagnose by symptom | none | Symptom-first entries: blank page; button does nothing; changes not appearing (save/reload); server won't start; code after start_server never runs [R]; slow first load (Pyodide boot) | 1R | errors index | students/help.md | P0 | create |
| `/help/errors/` | Error index | S | Idx | — | Find an entry from exact error text | none | Search-first page; entries listed by the exact technical error string and by friendly title; mapping maintained against `error_explainer.py` tables [R] | 0 | all entries | data/error_explainer.py [R] | P0 | create |
| `/help/debug-panel/` | The debug panel in depth | S | How | L2 | Use all five tabs | start/debug-panel | Current (state view/edit), History (time travel), Overview (routes, route graph), Tests, Environment (files, packages, config, log); badges; save/load state; theme switcher | 2R | build/regression-tests | js/src/debug [R] | P1 | create |
| `/help/bug-reports/` | Report a Drafter bug | S | How | — | File a useful bug report | none | Bug vs homework question (mirrors `--bug-report` route [R]); the Download Bug Report button; what the bundle contains; where to send | 0 | help index | router/defaults/bug_report.py [R] | P1 | create |
| `/help/faq/` | FAQ | S | Ref | — | Quick answers | none | Seeded from real course questions [A]; each answer links to the full page | 0 | varies | new | P2 | create |

Error entries (all: Aud S, Type Trb, content TRB7 = original error preserved → plain-language meaning → likely location → discriminating checks → minimal fix → confirm → prevent → concept link; each with 1 runnable minimal reproduction where feasible; Priority P1 unless noted; Status create; Source: `error_explainer.py` tables + curated examples [R]):

| Proposed URL (under `/help/errors/`) | Page title (error family) | Level | Concept link | Pri |
|---|---|---|---|---|
| `route-not-found/` | Link or button points to an unknown route | L2 | learn/routes-and-pages | P0 |
| `missing-parameter/` | Route is missing a parameter a form expected | L2 | learn/forms-and-input | P0 |
| `type-conversion-int/` | Could not convert text to an int ("use float" hint) | L2 | learn/forms-and-input | P0 |
| `type-conversion-other/` | Could not convert a value to the parameter's type | L2 | learn/forms-and-input | P1 |
| `state-mismatch/` | State doesn't match the State class (changed fields) | L2 | learn/state | P0 |
| `nothing-after-start-server/` | Code after start_server() never runs | L1 | reference/start-server | P0 |
| `page-content-invalid/` | Page content must be a list of strings/components | L1 | reference/page | P0 |
| `duplicate-component-name/` | Two components share a name | L2 | learn/forms-and-input | P1 |
| `selectbox-default-missing/` | SelectBox default not in options | L3 | input/selectbox | P1 |
| `header-level-invalid/` | Header level must be 1-6 | L2 | text/header | P2 |
| `circular-reference-tests/` | "Circular Reference" appears in generated tests | L3 | build/regression-tests | P1 |
| `file-decode-error/` | Uploaded file couldn't be read as text | L3 | build/files | P1 |
| `missing-asset-on-deploy/` | Image/file works locally but 404s when deployed | L2 | build/deploy | P0 |
| `deploy-build-failed/` | GitHub Actions build failed | L2 | build/deploy/troubleshooting | P0 |
| `package-import-error/` | A library import fails in the browser | L3 | extend/packages | P1 |
| `permission-denied-device/` | Camera/microphone/location permission denied | L4 | relevant component | P2 |

[REC] The seeded 16 are a floor. Phase H (§10) includes mining `error_explainer.py`'s `ID_EXPLANATIONS`/`EXCEPTION_EXPLANATIONS` tables so every curated friendly message has a corresponding entry or explicit exclusion.

### 5.8 Teach (instructor area, dark scheme)

| Proposed URL | Page title | Aud | Type | Level | Learner goal | Prerequisites | Required content | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/teach/` | Teaching with Drafter | T | Idx | — | Orient instructors | none | Banner + scheme switch; section map; "students: you probably want /start/" | 0 | all teach | new | P1 | create |
| `/teach/why-drafter/` | Why Drafter | T | Con | — | Evaluate Drafter for a course | none | Pedagogy rationale (routes as pure-ish functions, dataclass state, testability); tradeoffs vs Flask/Django (real backend), Streamlit (widget model), raw HTML/JS; honest limits (no backend, Pyodide boot time, no persistence) | 0 | extend/pyodide | ARCHITECTURE.md; new | P1 | create |
| `/teach/big-ideas/` | The big ideas | T | Con | — | Know what to emphasize when teaching | why-drafter | The 8-10 concepts in teaching order: route/page mapping, state threading, name→parameter contract, type conversion, testing routes as functions, runtime model, deployment as compilation | 0 | learn section | new | P1 | create |
| `/teach/beyond-the-basics/` | Beyond the student docs | T | Ref | — | Know the advanced surface | big-ideas | Fragment/Update/Redirect; events; persistent components; audio/camera/map families; configuration system; CLI; shared-runtime embedding; what is deliberately not shown to students | 0 | extend, reference | agent findings [R] | P1 | create |
| `/teach/lesson-plans/` | Lesson plans | T | Idx | — | Pick a plan | none | Index + 3 seed plans (first day with Drafter; forms and state lab; testing lab), each on the §7.9 template | 0 | plans | new | P2 | create |
| `/teach/lesson-plans/<3 seeds>` | (three plans) | T | Les | — | Run a class session | varies | §7.9 template each | links to playground | learn pages | new | P2 | create |
| `/teach/project-ideas/` | Project ideas | T | Ref | — | Assign well-scoped projects | none | 15-20 ideas rated by scope and concepts exercised; anti-patterns (real auth, realtime multiplayer, heavy data) | 0 | build/final-project | new; secret_examples inspiration [A] | P2 | create |
| `/teach/student-misconceptions/` | Student misconceptions | T | Mis | — | Anticipate and repair misconceptions | big-ideas | §7.10 template entries: state is shared/persistent; routes run top-to-bottom like scripts; the server is remote; login is secure; tests must match pages exactly; styling changes state | 0 | learn pages | new [A: seed from experience] | P1 | create |
| `/teach/expert-misconceptions/` | Expert misconceptions | T | Mis | — | Correct experienced-dev assumptions | none | Entries: "it's like Flask" (no backend); "state is a session" (in-memory, per-tab); "deploy needs a server" (static); "hidden source is safe" (it isn't); "it renders server-side" (browser) | 0 | extend/pyodide, why-drafter | new | P1 | create |
| `/teach/classroom/` | Classroom logistics | T | How | — | Run Drafter robustly in class | none | Rubric starting points; contingencies: CDN/Pyodide offline plans, lab-machine installs, projector-friendly themes; grading via `--about` and tests | 0 | build/deploy | new [I] | P2 | create |

### 5.9 Extend

| Proposed URL | Page title | Aud | Type | Level | Learner goal | Prerequisites | Required content | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/extend/` | Extend | S | Idx | L4 | Orient advanced students | core L2 | Section map; "you don't need this for most projects" framing | 0 | all extend | new | P1 | create |
| `/extend/pyodide/` | Python in the browser | S | Con | L4 | Accurate deeper runtime model | how-drafter-works | Pyodide/WASM in one screen; the two runs in detail; boot cost; virtual filesystem; the `js` module exists (pointer, not tutorial) | 1R | dev/architecture | ARCHITECTURE.md | P1 | create |
| `/extend/javascript/` | JavaScript interop | S | How | L4 | Call JS when Python isn't enough | pyodide | Page `js`/`css` params; `js` module basics with 2 worked recipes; custom elements exist (pointer to custom-components); caveats | 2R | custom-components | payloads css/js [R] | P2 | create |
| `/extend/custom-components/` | Build your own components | S | How | L4 | Create reusable components | javascript | Level 1: helper functions returning component trees [R: custom_component.py]; Level 2: RawHTML/HtmlTag; Level 3: custom JS elements (overview + dev-docs pointer) | 3R | dev docs | custom_component.py [R] | P2 | create |
| `/extend/packages/` | Third-party libraries | S | How | L4 | Use pandas, matplotlib, etc. | install | Auto-loading detection [R]; what works in Pyodide vs not; matplotlib on demand; pandas basics; requests caveats (CORS); declaring project packages | 2R | media/matplotlibplot, help/errors/package-import-error | README flags [R], fetch_weather.py | P1 | create |
| `/extend/performance/` | Performance | S | How | L4 | Keep apps responsive | core | Boot time expectations; big state costs (deep copies [R]); image sizes; too many components; Fragment instead of full re-render | 1R | live-updates | ARCHITECTURE.md | P2 | create |
| `/extend/security/` | Security honestly | S | Con | L3 | Know exactly what is and isn't protected | how-drafter-works | Everything ships to the browser; no secrets in code; login demos are simulations; validation is UX not security; safe handling of user text (escaping [R]); when you need a real backend | 1R | examples/login, teach/expert-misconceptions | new [I] | P1 | create |
| `/extend/flask/` | Moving on to Flask | S | Tut | L4 | Bridge to a backend framework | core | Retained migration guide, refreshed against v2 idioms | 0 | teach/why-drafter | reference/flask.md | P2 | revise |

### 5.10 Developers

| Proposed URL | Page title | Aud | Type | Level | Learner goal | Prerequisites | Required content | Examples | Related pages | Source material | Pri | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/dev/` | Developer documentation | D | Idx | — | Orient contributors | none | Banner + scheme; map; "students: see Reference" redirect card | 0 | all dev | new | P1 | create |
| `/dev/architecture/` | Architecture | D | Con | — | Understand the system design | none | ARCHITECTURE.md migrated/refreshed (fix stale theme list [R]); diagrams | 0 | internals-map | ARCHITECTURE.md | P1 | revise |
| `/dev/api/` | Full API reference | D | Ref | — | Authoritative per-module docs | none | mkdocstrings-generated per-module pages (`--api` builds [R]); each page: import, signature, params/types/defaults, returns, side effects/lifecycle, errors, security/a11y implications, tested example, links to how-to/concept and external depth | generated | reference | tools/gen_ref_pages.py [R]; DOCUMENTATION_PLAN.md | P1 | revise |
| `/dev/contributing/` | Contributing | D | How | — | Set up and validate a dev environment | none | uv setup, JS watchers, test suites, just recipes (from README §Development) | 0 | docs-guide | README.md | P2 | create |
| `/dev/docs-guide/` | Writing documentation | D | How | — | Author pages that pass CI | contributing | Templates catalog; front-matter schema; drafter-fence usage (hl_lines, height, editable); coverage/lint/link CI; style rules (§3.9-3.10) | 1R | templates | this plan; mkdocs plugin [R] | P1 | create |
| `/dev/internals-map/` | Internals map | D | Ref | — | Find the right module fast | architecture | Table: subsystem → package → key modules (bridge, client_server, router, payloads, components, config, builder, testing, debug JS) | 0 | api | README repo layout; ARCHITECTURE.md | P2 | create |

---

## 6. Example and content conventions

### 6.1 Example code standards [I]

- **Names**: accurate, plain-English, PEP 8 (`snake_case` functions/variables, `CapWords` dataclasses, `UPPER_CASE` constants). A canonical name glossary keeps examples consistent site-wide: `State`, `index`, `state`, and recurring domain names (`add_item`, `remove_item`, `show_result`, `save_score`...). No jargon names (`ctx`, `cfg`, `mgr`), no cute names in instructional code.
- **Structure**: one responsibility per function; shared page furniture extracted into helper functions once a pattern repeats; routes stay short (build content lists, mutate state, return a payload).
- **Allowed constructs only** (§2): no dicts, exceptions, comprehensions, lambdas, or `break` in student-facing examples. L4/Extend pages may relax this with an explicit "this uses X, which your course may not have covered" note.
- **Completeness**: every example is copyable as-is: includes its imports, its `State`, and `start_server(...)` (the docs plugin auto-appends `start_server()` when omitted [R], but published code shows it explicitly so copies work outside the docs).
- **Tests**: worked examples and tutorials include 1-3 Drafter assertions (`assert_state` for logic, `assert_has`/`assert_in` for presence) rather than brittle whole-page `assert_page` snapshots; regression-test pages are the exception where whole-page freezing is the topic.
- **Two spaces of quality control**: a fence linter enforces naming and allowed-construct rules mechanically (§11), and review enforces judgment calls.

### 6.2 Example indexing metadata [I][REC]

Every runnable example (fence or page) carries front-matter (or fence-adjacent comment metadata) with: `goal` (learner phrasing), `symbols` (API names used), `concepts`, `prereqs`, `level`, `context` (app domain), `runtime` (none / network / camera / microphone / location), and, for troubleshooting repros, `error_text` (the exact string). A gen-files script builds the Examples tag index and the per-symbol "used in these examples" strips on reference pages from this metadata. Coverage is evaluated against learner needs and API symbols (every exported symbol should appear in at least one runnable example or carry an explicit exclusion), not against a fixed example count.

### 6.3 Cross-linking rules [I]

- Reference → concept ("why does this work this way?") and → how-to ("common tasks with this").
- How-to → reference (exact parameters) and → error entries (what typically goes wrong).
- Error entry → the concept that repairs the misconception.
- Every L1/L2 page ends with a "Next" card chosen by likely next question, not by nav order.
- Deeper treatments are linked, never inlined: e.g. `Image` reference links to Picture type page and the images how-to instead of repeating them.

---

## 7. Page templates

All templates share front-matter: `template`, `title`, `level` (L1-L4 where applicable), `audience`, `prereqs` (list of page slugs), `symbols` (API names covered), `outcome` (one sentence: expected result of reading), plus §6.2 example metadata. The template linter (§11) enforces required headings per template. All templates require: alt text on every image, headings in order without skips, code fences with language tags, no color-only meaning, and reduced-motion-safe media. Where a page's topic has a real failure mode, a "Common problems" section is required and links into `/help/errors/`.

### 7.1 Quickstart tutorial (`template: tutorial`)

Required: **What you'll build** (with finished screenshot) → **What you need** (prereqs + time estimate) → numbered steps, each = runnable fence + "What this means" + a predict-or-modify prompt → **Common problems** → **What you learned** (vocabulary recap) → **Next steps** (cards). Testing: every fence compiles and runs in CI; final program's assertions pass. Accessibility: steps operable keyboard-only in embedded demos; screenshots have alt text describing state, not pixels.

### 7.2 Conceptual explanation (`template: concept`)

Required: **In one sentence** → **The idea** (prose + diagram where causal) → **See it** (1+ runnable fence with cause→effect annotation) → **What this means for your code** (consequences list) → **Where people get confused** (misconception-aware corrections) → **Go deeper** (links to advanced/Extend treatment). Testing: fences in CI; diagram source (mermaid) versioned in-page. Accessibility: diagrams get text equivalents (the mermaid source plus a prose summary).

### 7.3 Task-oriented how-to (`template: how-to`)

Required: **Goal** ("You want to...") → **Before you start** (prereqs, expected result) → **Steps / Recipes** (each recipe: smallest complete runnable fence + annotation + safe change points) → **Variations** → **Common problems** → **Related** (reference + concept links). Testing: every recipe runs in CI. Accessibility: recipes verified keyboard-operable where interactive.

### 7.4 Component reference (`template: component`, "CRT")

Required: **Name** (+ group, level badge, aliases) → **Description** (one paragraph, when-to-use) → **Syntax** (canonical constructor line(s)) → **Parameters** (table: name, type, default, constraints, meaning) → **Examples** (1-3 runnable, smallest-meaningful first) → **Notes** (behavior details, failure modes, performance/permission/persistence notes as applicable) → **Accessibility** (labeling, keyboard behavior; required for input/media components) → **Related components** (auto adjacency strip from group + hand-picked) → **External links** (MDN element, upstream library). Testing: parameter table checked against the actual signature by the coverage tool (§11); examples in CI. Family pages (inline text, page regions, effects) repeat Syntax/Parameters/Example per member under one page.

### 7.5 Full API reference (`template: api`, dev area)

Required (per module/symbol, mkdocstrings-rendered from docstrings): canonical import + signature → parameter meanings/types/constraints/defaults → return behavior → state changes, side effects, lifecycle → errors and warnings → security/accessibility implications → minimal tested example with expected output → links to how-to/concept pages → external depth links. Testing: docstring examples doctest-able where feasible; DOCUMENTATION_PLAN.md governs docstring completeness [R].

### 7.6 Runnable example (`template: example`)

Required: **What it does** (+ screenshot) → **Try it** (embedded, editable where enabled) → **The code** (full listing, annotated) → **How it works** (causal walkthrough keyed to line ranges) → **Make it yours** (ordered modify → complete → combine → create prompts) → **Tests** (included assertions explained) → **Likely errors** → **Related**. Testing: program + assertions run in CI. Accessibility: embedded demo passes keyboard/contrast checks.

### 7.7 Troubleshooting entry (`template: error`, "TRB7")

Required, in order: **The error** (exact original technical text, verbatim, searchable) → **What it means** (plain language) → **Where to look** (likely source location) → **Check** (discriminating diagnostics separating look-alike causes) → **Fix** (minimal repair with before/after code) → **Confirm** (how to verify it's gone) → **Prevent** (habit or pattern) → **Understand** (concept link). Front-matter carries `error_text` and `error_id` (matching `error_explainer.py` ids where applicable [R]). Testing: repro fence (where feasible) actually produces the documented error string in CI; `error_text` uniqueness checked.

### 7.8 Project gallery entry (`template: gallery`)

Required: **Pitch** (one paragraph + hero screenshot) → **Try it** (button launching the compiled app on its own page, new tab) → **Concepts used** (tag strip linking to docs) → **Tour of the code** (annotated source, sectioned; full source viewable/downloadable) → **State and routes** (state diagram + route map) → **Remix it** (download + 3 graded remix challenges) → **Credits/license**. Testing: app compiles in the gallery build pipeline; launch link checked; source download archives verified. Accessibility: the compiled app itself must pass the embedded-app accessibility bar (§11).

### 7.9 Teacher lesson plan (`template: lesson`)

Required: **Session goal** → **Audience and timing** → **Prerequisites** (student state before class) → **Materials** (docs pages, playground collections, starter files) → **Plan** (timed segments: warmup / demo / guided practice / independent / wrap) → **Checks for understanding** → **Common stumbles** (linked misconceptions) → **Extensions** → **Assessment ideas**. Testing: linked materials exist (linkcheck); starter files run in CI.

### 7.10 Misconception entry (`template: misconception`)

Required: **The belief** (stated as the holder would) → **Why it's plausible** → **What's actually true** → **How it shows up** (symptoms in student code/questions) → **How to repair** (explanation move, demo, or activity, with links) → **Related docs**. Grouped list pages hold many entries; each entry is anchor-addressable.

---

## 8. Content migration map

Disposition of every existing file under `docs/`. "→" names destination page(s) from §5. Old URLs receive redirects [Q: redirects plugin to be added].

| Current file | Disposition | Destination(s) / notes |
|---|---|---|
| `index.md` | revise (rewrite) | `/` home; fix broken quickstart link [R] |
| `quick/quickstart.md` | revise (expand) | `/start/first-app/`; keep structure, add debug-panel handoff, fix "usally" typo, drop "New" from title |
| `multiple_examples.md` | remove (from site) | Becomes an internal perf fixture outside nav (move under a CI-only path); title typo moot |
| `students/installation.md` | revise | `/start/install/`; fix broken quickstart links |
| `students/docs.md` | split + merge | Superseded: concept material → `/learn/routes-and-pages/`, `/learn/forms-and-input/`; per-component text merged into CRT pages; config functions → `/reference/site-config/`; then remove |
| `students/html.md` | revise | `/build/html/` |
| `students/styling.md` | split | `/build/styling/` (overview), `/build/styling/themes/`, `/build/styling/helpers/`, `/build/styling/custom-css/`, `/reference/styling-functions/`, `/reference/themes/`; fix broken fences [R]; correct theme list against registry [R] |
| `students/pictures.md` | split | `/build/images/` (how-to) + `/reference/data-types/picture/`; resolve the two TODO markers [R] |
| `students/testing.md` | revise + split | `/build/testing/` (bulk retained) + `/build/regression-tests/` + `/reference/testing-functions/` |
| `students/console.md` | revise | `/build/printing-and-console/`; verify `--console-mode` flag claim [Q] |
| `students/deployment.md` | split | `/build/deploy/` + `/prepare/` + `/github-pages/` + `/troubleshooting/` + `/course-checklist/` [Q]; move generic web-URL explanation to `/learn/how-the-web-works/` |
| `students/help.md` | split | Symptom entries → `/help/troubleshooting/`; circular-reference → `/help/errors/circular-reference-tests/`; fix unclosed-paren snippet bug [R] |
| `examples/examples.md` | revise (rebuild) | `/examples/` tag index |
| `examples/calculator.md` | revise | `/examples/calculator/`; deliver or drop the promised extra versions [R] |
| `examples/ring.md` | revise | `/examples/ring/`; unify `@route` style |
| `examples/forms.md` | revise | `/examples/forms/`; make runnable; add missing import [R] |
| `examples/login.md` | revise | `/examples/login/`; make runnable; strengthen security disclaimer |
| `examples/nested_data.md` | revise (rename) | `/examples/pet-registry/`; make runnable |
| `workbook/index.md` | revise | `/learn/tutorials/` |
| `workbook/part1/cookie.md` | revise | `/learn/tutorials/cookie-clicker/`; host starter files in docs assets (docsrc/ is gone [R]); remove "Bottle backend" output |
| `workbook/part2/bank.md` | revise | `/learn/tutorials/bank-account/`; same starter-file fix |
| `workbook/part3/adventure.md` | revise | `/learn/tutorials/adventure-game/`; same + restore images |
| `workbook/part4/store.md` | revise | `/learn/tutorials/store/`; align with v2 debugger UI wording |
| `reference/reference.md` | revise | `/reference/` |
| `reference/components.md` | merge | Into `/reference/components/` master list (the tag/HTML mapping survives as a column) |
| `reference/colors.md` | retain | `/reference/colors/` |
| `reference/fonts.md` | retain | `/reference/fonts/` |
| `reference/flask.md` | revise | `/extend/flask/` |
| `components/basic/index.md` | merge | Into `/reference/components/` (group intro text) |
| `components/basic/{text_box,text_area,button,link,check_box,numbered_list,bulleted_list,argument}.md` | revise | Corresponding CRT pages (§5.6); these are the template baseline; fix noted typos/URLs |
| `components/advanced/index.md` | merge | Into `/reference/components/` |
| `components/advanced/{image,table,select_box}.md` | revise | CRT pages; fix "Fih" [R] |
| `components/advanced/formatting/*.md` (6 files) | revise/split | CRT pages; `div_row.md` splits into Div and Row pages; fix "USing", tab/space mixing [R] |
| `components/advanced/files/*.md` (3 files) | revise | FileUpload and Download CRT pages; index merges into master list |
| `components/specialized/index.md` + `matplotlib/index.md` | remove (superseded) | Replaced by real specialized CRT pages (§5.6) |
| `extra.css` | remove (superseded) | Replaced by the design system (§9) |
| `mkdocs.yml` nav | remove (rebuild) | Entire nav rebuilt to §4; current nav references nonexistent `ComponentDocs/**` and `quick start new/` paths [R] |

Also migrating from outside `docs/`: `ARCHITECTURE.md` → `/dev/architecture/` (source file stays; page generated or mirrored [REC]); README quick-start/CLI tables → `/reference/start-server/`, `/reference/cli/`, `/dev/contributing/`; curated `examples/*.py` → playground collections and worked examples per §5.4 (the ~20 internal QA harness files are deliberately excluded [R]).

---

## 9. Theme specification

### 9.1 Goals and constraints

Professional, friendly, clear; a light "blueprint/draft" motif that never competes with content [I]. Three visually distinct zones: student (light, default), Teach (dark navy), Developers (dark graphite) [I]. WCAG 2.2 AA throughout [I]. Front page calm, with unmistakable next steps [I].

[REC] Implementation approach: keep mkdocs-material as the base and build the identity as a Material customization layer (palette + fonts + `overrides/` partials + CSS). A from-scratch theme would cost weeks and re-solve search, nav, and i18n. This inherits Material's accessibility baseline and keeps the drafter-codeblocks plugin untouched. [Q: the properdocs runner question (§14) must be settled first, since the theme layer targets whatever MkDocs core the site builds with.]

### 9.2 Design tokens

Colors (all pairs contrast-checked; values are starting points for the designer, not final):

| Token | Light (student) | Dark (student) | Teach | Dev |
|---|---|---|---|---|
| Background | `#FAFBFD` paper | `#111827` | `#0F172A` deep navy | `#16181D` graphite |
| Surface/card | `#FFFFFF` | `#1A2332` | `#16213B` | `#1E2128` |
| Ink/text | `#1D2A38` | `#E6EAF0` | `#DCE4F2` | `#DDE1E6` |
| Primary (blueprint blue) | `#1D5DBF` | `#6EA8FF` | `#7FB0FF` | `#4FC3E8` cyan |
| Accent (annotation) | `#C4610C` amber, sparing | `#E8A04C` | `#E8B93E` | `#B48CFF` violet |
| Grid line (motif) | `#E3EBF5` | `#233047` | `#1D2B4A` | `#262B33` |
| Success / warn / error | standard AA-checked triad, each paired with an icon + text label (never color-only) | | | |

Typography: body Inter (or Source Sans 3) at 16px minimum, line-height 1.6, measure capped ~72ch; headings same family, weight-differentiated; code JetBrains Mono 0.9em with ligatures off. All type in rem; layout honors 200% zoom and 320px reflow (WCAG 1.4.4/1.4.10).

Blueprint motif, deliberately quiet:
- Faint grid background only in the hero band, section-index headers, and empty-state illustrations, never behind body text.
- Runnable-demo frames styled as "drafting sheets": 1px solid border, small corner tick marks, a title-block strip (example name + Run/Edit/Reset controls + level badge).
- Dashed rules for "draft"/work-in-progress callouts; solid rules elsewhere.
- Small compass/pencil line icons for section identity; no watermark imagery.
- `prefers-reduced-motion` disables all decorative transitions; page-transition effects are opt-in and subtle.

### 9.3 Component styles

- **Page-type and level badges**: pill labels (Tutorial / Concept / How-to / Reference / Example / Troubleshooting) and level chips ("First steps", "Core", "Advanced", "Specialized"), each icon + text.
- **Page header block**: renders the front-matter contract — purpose line, prerequisites (linked), "you'll be able to..." outcome, and estimated time on tutorials.
- **Next-step cards**: end-of-page card row driven by front-matter.
- **Admonitions**: mapped to a restrained set (Note, Careful, Deeper) in motif styling.
- **Component adjacency strip**: auto-generated "Other input components:" chips on CRT pages.
- **Error-entry header**: monospace verbatim error block visually distinct (this is what students paste-search).
- **Zone banners**: Teach and Dev pages show a slim full-width banner naming the zone with a "student docs" return link; zone accent colors persist in nav/sidebar so a lost student notices immediately.

### 9.4 Front page composition [I]

Single screen above the fold: wordmark + one-sentence pitch; a small tasteful animated-or-static counter demo (static image fallback, reduced-motion honored); three equal cards — **Start the tutorial** (primary), **See examples**, **Find a component**; below the fold: "Already deployed once?" quick links (styling, testing, deploying), then quiet single-line links to Teach and Developers. No wall of section links, no changelog, no badges.

### 9.5 Accessibility engineering requirements (theme-level)

Skip-to-content link; visible 2px focus outlines on all interactive elements including embedded-demo controls; landmark roles; `aria-live=polite` announcements for demo run/build status and theme switches; keyboard-operable code editors with documented Escape hatch (Esc then Tab); all information conveyed by color duplicated in text/icon; contrast AA verified per token pair in both schemes; iframes titled; demo iframes get accessible names from their example titles.

---

## 10. Implementation phases

Ten phases, A-J, in required sequence (C and the content phases D-I can partially overlap once B lands). Every phase lists the eight required fields. Priorities: P0 pages = phases B-D; P1 = through I; P2 items may trail into post-release iterations.

### Phase A — Discovery and decisions

- **Objective**: convert this plan's [Q] items into decisions; verify the flagged technical unknowns.
- **Included**: stakeholder review of this document; spike verifying: the app-container CSS selector for the styling-gotchas page, the `--console-mode` flag, redirects plugin choice, editable-embed performance on a 8-demo page, gallery compile pipeline feasibility; decisions on properdocs, `RadioButtonGroup`/`change_text_transform` exports, `set_website_theme` alias, course-checklist placement, gallery seed projects and `secret_examples` permission.
- **Dependencies**: none.
- **Deliverables**: decision log appended to this file; spike notes; corrected API export list if changed.
- **Validation**: every §15 question has an owner and an answer or an explicit deferral.
- **Exit criteria**: zero unowned [Q] items blocking phases B-D.
- **Risks**: decisions stall; mitigate with a default-if-no-answer column in the decision log.
- **Deferred**: all content work.

### Phase B — Information architecture and scaffolding

- **Objective**: stand up the new site skeleton with working CI before content lands.
- **Included**: new `mkdocs.yml` nav per §4; directory scaffold with stub pages carrying final front-matter; front-matter schema; template linter, coverage auditor (extending `tools/doc_audit.py` [R]), fence-runner CI job, linkcheck; redirects plugin wired with the §8 map; `multiple_examples.md` moved to a CI-only fixture.
- **Dependencies**: A (redirects/properdocs decisions).
- **Deliverables**: building site with complete nav of stubs; CI red/green on the four checks; `dev/docs-guide/` first draft (authors need it now).
- **Validation**: CI runs on a PR touching a stub; old-URL redirect spot checks; strict-mode build passes (no missing-nav warnings).
- **Exit criteria**: `drafter-docs build` strict-clean; all §5 URLs resolve to stubs or pages; the four CI checks are required on the docs path.
- **Risks**: nav churn later — mitigated by treating §5 URL column as the contract.
- **Deferred**: visual design (stubs use default Material).

### Phase C — Design system and theme

- **Objective**: implement §9 as a Material customization layer with the three zones.
- **Included**: tokens, typography, motif CSS, page-header/badge/next-card partials, demo-frame styling, zone banners and schemes, front page, accessibility engineering (§9.5).
- **Dependencies**: B (front-matter drives the partials).
- **Deliverables**: theme layer in-repo; themed front page; a "template zoo" page rendering every template with dummy content in all zones/schemes.
- **Validation**: axe/pa11y clean on the zoo page in light/dark/Teach/Dev; manual keyboard walkthrough incl. an embedded editable demo; contrast audit of every token pair; reduced-motion check.
- **Exit criteria**: zoo page passes automated a11y with zero serious violations; stakeholder sign-off on look.
- **Risks**: motif overwhelms readability — mitigated by the zoo review before content styling debates; properdocs/Material version drift.
- **Deferred**: theme-catalog screenshot automation (Phase E); gallery card design polish (Phase G).

### Phase D — Minimum viable student pathway (all P0 pages)

- **Objective**: a student can install, build a first app, understand the model, style it, test it, and deploy it using only new pages.
- **Included**: Home; Start (4 P0 pages); `how-drafter-works`, `routes-and-pages`, `state`, `forms-and-input`; Build P0 set (multiple-pages, collect-input, show-data, styling×3, testing, deploy×4); Reference P0 set (components master list, page, route, start-server, site-config, styling-functions, themes catalog v1, 11 L2 component pages); Examples P0 (index v1, calculator, ring, forms); Help P0 (index, troubleshooting, errors index, 6 P0 error entries).
- **Dependencies**: B; C at least for header/demo partials.
- **Deliverables**: ~45 finished pages, all fences green in CI.
- **Validation**: end-to-end cognitive walkthrough: 2-3 target-population students (or proxies) run install→first-app→restyle→test→deploy while observed; time-to-first-success and stuck points recorded; deployment guide task-tested start-to-finish on a fresh GitHub account.
- **Exit criteria**: walkthrough completers reach a deployed app without consulting old docs; all P0 rows in §5 shipped; coverage tool reports every P0-listed symbol documented.
- **Risks**: deployment guide still overwhelming — the walkthrough is the test; split further if observed.
- **Deferred**: everything P1/P2.

### Phase E — Core reference

- **Objective**: complete the reference layer: all 57 component pages, remaining function/type/theme pages, keyword-attributes, CLI.
- **Included**: §5.5 + §5.6 P1 rows (P2 component pages may trail); theme-catalog preview generation (scripted screenshots of one canonical demo in all 20 themes); adjacency strips; per-symbol example strips from §6.2 metadata.
- **Dependencies**: D (templates proven on the P0 set).
- **Deliverables**: full component reference; coverage tool green against `__all__` (174 names documented or explicitly excluded with reasons).
- **Validation**: coverage CI gate flips from report-only to blocking; parameter tables machine-diffed against signatures; spot review of 10 random pages against CRT.
- **Exit criteria**: zero undocumented exported names without a recorded exclusion; all CRT-required sections present per linter.
- **Risks**: 57 pages is the volume peak — mitigate with the CRT generator producing pre-filled skeletons from signatures (extend `tools/doc_audit.py`); quality drift across authors — mitigate with the linter + a rotating reviewer.
- **Deferred**: L4 sound/media P2 pages may land in the first post-release cycle without blocking release.

### Phase F — Examples, playground, worked examples

- **Objective**: the Examples section becomes the site's center of gravity.
- **Included**: tag-index rebuild; worked examples (login, pet-registry, todo-list, shop, photo-editor); playground index + P1 collections (basics, forms, lists-and-tables, styling); editable embeds enabled and load-tested; §6.2 metadata across all examples; P2 collections (media, interactive, sensors) as capacity allows.
- **Dependencies**: E (examples link into reference); C (demo frames).
- **Deliverables**: ~15 example/playground pages; tag index auto-built; runtime-requirement labels (camera/mic/location/network) on every demo.
- **Validation**: all demos compile + run in CI; page-weight/boot measurement on the largest collection page (shared runtime must keep it usable on a mid-range laptop [Q threshold set in Phase A]); example-coverage report by concept and symbol.
- **Exit criteria**: every L1/L2 concept has ≥2 runnable examples reachable from the tag index; playground P1 collections live.
- **Risks**: multi-demo page memory pressure (shared runtime mitigates but is not free [R]); editable embeds on low-end hardware — fallback is read-only + "open in playground".
- **Deferred**: sensors collection can trail (device-permission demos are hard to CI).

### Phase G — Project gallery

- **Objective**: ship the gallery: full apps compiled to standalone pages with source access.
- **Included**: gallery build pipeline (per-project `--compile` into `gallery/<slug>/` with metadata catalog); index page; 4-6 seed entries per §7.8; remix download packaging.
- **Dependencies**: A (seed selection/permissions), C (cards), F (template conventions).
- **Deliverables**: pipeline script + CI job; gallery index; seed entries live, each launching its compiled app.
- **Validation**: each app compiles reproducibly in CI; launch links + downloads checked; each app manually smoke-tested on desktop + mobile widths; a11y scan of gallery pages and one compiled app.
- **Exit criteria**: ≥4 entries live with working try-it and source access.
- **Risks**: this is the largest new engineering item — timebox and ship with 4 entries rather than slip; `secret_examples` permission may fall through (fallback: expand shop/adventure ourselves).
- **Deferred**: community submissions process; gallery filtering UI beyond simple tags.

### Phase H — Help and error system

- **Objective**: complete the searchable error index and deep help content.
- **Included**: remaining error entries (mine `error_explainer.py` `ID_EXPLANATIONS`/`EXCEPTION_EXPLANATIONS` so every curated friendly message maps to an entry or a recorded exclusion [R]); debug-panel deep guide; bug-reports page; FAQ seeding; error-repro CI harness.
- **Dependencies**: D (error template proven); E (concept links exist).
- **Deliverables**: ≥16 entries + explainer-parity report; `/help/debug-panel/`; `/help/bug-reports/`.
- **Validation**: paste-search test: for each entry, pasting the exact error text into site search returns the entry first; repro fences produce the documented strings in CI.
- **Exit criteria**: explainer-parity report shows 100% mapped-or-excluded; paste-search test passes for all entries.
- **Risks**: error strings drift as the explainer evolves — the parity CI check is the guard.
- **Deferred**: analytics-driven prioritization of new entries (needs post-launch data).

### Phase I — Teach, Extend, Developer areas

- **Objective**: complete the three non-core zones.
- **Included**: §5.8 Teach pages (misconception lists P1, lesson plans/project ideas P2); §5.9 Extend pages; §5.10 Dev pages incl. `--api` build wiring into `/dev/api/` and the docs-guide finalization.
- **Dependencies**: C (zone schemes), E (teach/extend link into reference).
- **Deliverables**: all P1 rows in §5.8-5.10; zone banners live; api build documented (slow `--api` builds remain opt-in [R]).
- **Validation**: zone-distinctiveness check with fresh eyes ("which zone am I in?" test); teacher review of misconception lists by at least one instructor beyond the author; dev-docs walkthrough by a new contributor.
- **Exit criteria**: P1 zone pages shipped; both banners and schemes verified in light/dark.
- **Risks**: teacher content quality depends on scarce instructor time — seed from this plan's research and iterate.
- **Deferred**: additional lesson plans; expert-misconception expansion.

### Phase J — Migration cutover, validation, maintenance handoff

- **Objective**: retire the old content, validate the whole, and lock in maintenance.
- **Included**: execute remaining §8 dispositions (delete superseded files, final redirect table); full-site validation pass; behavioral evaluation study; maintenance runbook.
- **Dependencies**: D-I.
- **Deliverables**: old pages removed/redirected; validation report; maintenance runbook in `/dev/docs-guide/` (release checklist, coverage gates, how to add a component page/example/error entry); backlog of P2 remainder.
- **Validation**: full linkcheck incl. inbound redirect checks; axe/pa11y across representative pages of every template in every zone; manual WCAG 2.2 AA audit of the five key flows (navigate, run a demo, edit a demo, read an error, search); behavioral study measuring time-to-first-success, task completion, navigation efficiency, error recovery, transfer (modify an unseen example) — reported separately from satisfaction/confidence surveys [I].
- **Exit criteria**: acceptance criteria (§17) all green; sign-off recorded.
- **Risks**: cutover breaking inbound course links mid-semester — schedule between terms [A]; validation findings forcing rework — reserve buffer.
- **Deferred**: localization; versioned docs (mike); community contribution process.

---

## 11. Testing and maintenance strategy

Documentation is versioned software [I]. Five automated gates, all wired in Phase B, all required on docs-touching PRs:

1. **Example execution.** The drafter-codeblocks plugin already compiles every ```` ```python drafter ```` fence at build time; compile failure fails the build [R]. Added: a pytest harness that extracts every fence (runnable and static `python` fences marked `test=true`), executes it under CPython with Drafter imported, and asserts (a) no exceptions before `start_server`, (b) every Drafter assertion in the code reports SUCCESS (routes are host-callable, so tests run without a browser [R]), (c) for error-entry repros, the emitted error contains the documented `error_text`. Exact copyable code is what's tested — no hidden setup [I].
2. **Coverage audit.** Extends `tools/doc_audit.py` [R]: parses `drafter.__all__` (174 names) and every page's `symbols` front-matter; reports names with no primary reference page and names never used in any runnable example; blocking after Phase E with an explicit, reasoned exclusion list (e.g. internal aliases). A second audit dimension checks concepts: a maintained concept list (state, routing, forms, conversion, testing, styling, deployment, persistence, security...) each mapped to a primary page.
3. **Template completeness.** Linter validates front-matter schema and per-template required headings (§7); reports incomplete pages with what's missing, so "identify what is still needed for incomplete pages" is a CI artifact, not a manual sweep [I].
4. **Links and structure.** Strict MkDocs build (no orphan/missing nav), lychee (or equivalent) for internal/external links, redirect-map verification, image alt-text presence check.
5. **Accessibility.** pa11y-ci/axe against a built-site page set covering every template × zone × scheme; keyboard smoke script for demo frames; contrast checked at token level in Phase C and re-verified on token changes.

Maintenance workflow: adding an exported name fails gate 2 until documented, which is the enforcement loop keeping docs and API in sync; adding a curated error explanation fails the Phase-H parity check until an entry or exclusion exists; the release checklist in `/dev/docs-guide/` ties `just validate` to a docs build.

Behavioral evaluation (separate from CI): instrument time-to-first-success during Phase D walkthroughs and the Phase J study; post-launch, periodic task-based probes (deploy task completion, error-recovery success on seeded bugs, unseen-example modification) reported separately from satisfaction surveys [I].

---

## 12. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Volume: ~170 pages overwhelms author capacity | High | Slip | Strict P0/P1/P2 discipline; CRT skeleton generation; family-page grouping already trims 20+ pages |
| properdocs fork dependency shifts under the theme layer [R] | Medium | Rework of theme/plugins | Resolve in Phase A; pin exact versions; keep the customization layer thin |
| Multi-demo pages too heavy on lab hardware | Medium | Playground unusable for target users | Shared runtime [R], lazy iframes [R], per-page demo budget, measured threshold in Phase F |
| Pyodide CDN dependency: offline/filtered classrooms | Medium | Demos dead in class | Document self-hosting (`--pyodide-url` [R]) in /teach/classroom/; static screenshots as fallback content |
| Docs build time balloons (compiling 200+ demos) | Medium | Slow CI, author friction | Plugin caches per-hash [R]; measure in Phase B; parallelize compiles if needed [Q] |
| v2 API still moving (beta) — docs churn | Medium | Stale pages | Coverage gate catches additions; signature diff catches changes; component pages generated partly from signatures |
| Gallery pipeline underestimated | Medium | Phase G slips | Timebox; ship 4 entries; pipeline is a plain loop over `--compile` [R] |
| secret_examples permission unavailable | Medium | Weaker gallery seeds | Fallback list named in Phase G |
| Students land in Teach/Dev zones and get confused | Low | Confusion | Zone banners, schemes, soft gating from student nav |
| Embedded demos themselves fail a11y (upstream app rendering) | Medium | AA target missed | Scope AA claim precisely in Phase A; file upstream issues; docs-side controls fully accessible regardless |
| Course-specific deployment content leaks back into generic pages | Medium | Overwhelming deploy guide returns | The split (§5.3) plus review rule: course terms (Canvas, instructor URL) only allowed on course-checklist |
| Old inbound links (course sites, LMS) break at cutover | High | Student disruption | Full redirect map (§8); cutover between terms [A] |

## 13. Assumptions [A]

1. The rewrite targets Drafter v2 on `v2-pyodide` only; v1 docs are out of scope and their site remains until cutover.
2. The documentation team can run the full local build (`uv run drafter-docs serve --dev`) per README.
3. At least one instructor (the maintainer) is available for Teach-content review and the Phase D walkthrough has access to 2-3 target-population students or close proxies.
4. The final-project course context (video, Canvas) applies to one institution and should not constrain the generic deploy guide.
5. Cutover can be scheduled between academic terms.
6. English-only for the first release (the JS layer has i18n parity tests, but docs localization is not in scope).
7. Seed misconception lists can be drawn from instructor experience without a formal study.

## 14. Contradictory source material [R]

1. **Nav vs filesystem**: `mkdocs.yml` nav references `ComponentDocs/**` and `quick start new/quickstart_new.md`, none of which exist; real pages (`reference/*`, workbook parts) are absent from nav. Resolution: rebuild nav (§8).
2. **properdocs**: `pyproject.toml` comments and `DOCUMENTATION_PLAN.md` describe keeping the properdocs fork *out* (pinning plugins to pre-coupling versions), yet `mkdocs_build.py` invokes `python -m properdocs` and it is a declared dev dependency. One of the two stances must win (Phase A).
3. **Theme lists disagree**: `students/styling.md` documents ~21 themes including `darkfairy` and `matcha`; the registry has 20 active with those two commented out; `ARCHITECTURE.md` lists a stale shorter set. Resolution: registry is authoritative; docs generate the catalog from it.
4. **`set_website_theme`**: one audit found it as an unexported alias in `deploy.py`; another concluded it doesn't exist. Verify in Phase A; document only the canonical `set_website_style` either way.
5. **Console mode**: `students/console.md` documents a `--console-mode` flag and `DRAFTER_CONSOLE_MODE` env var; the README flag tables and `start_server` parameter list don't show it, while the JS layer clearly implements the four modes. Verify the actual configuration surface in Phase A.
6. **`docs/index.md` and `students/installation.md`** link to a `quickstart/` directory that doesn't exist (actual: `quick/`).
7. **Workbook starter links** point into the deleted `docsrc/` tree.
8. **`examples/calculator.md`** promises multiple calculator versions but contains one.

## 15. Unresolved questions and decisions requiring stakeholder input [Q]

Technical verifications (Phase A spike):
1. Exact CSS selector for the app container vs `body` (needed for `/build/styling/gotchas/`), and whether a stable documented class exists for students to target.
2. The real configuration surface for console modes (flag? `start_server` kwarg? env only?).
3. Whether `set_website_theme` exists as an alias, and whether to export it.
4. Redirects mechanism (mkdocs-redirects plugin compatibility with the properdocs runner).
5. Editable-embed performance envelope: max demos per page on target hardware; whether editable is default-on or per-fence opt-in.
6. Docs build time at ~200 demos; caching/parallelization needs.
7. Whether error-repro fences can run against the friendly-error layer host-side (some errors may only materialize in the browser path).

Stakeholder decisions:
8. **properdocs**: adopt openly (and document why) or revert to mainline MkDocs. Blocks theme work.
9. **Export gaps**: `RadioButtonGroup` and `change_text_transform` are implemented but missing from `__all__` — fix the exports (recommended) or document them as internal? The docs plan assumes they will be exported.
10. **Course-checklist placement**: keep `/build/deploy/course-checklist/` in the main site, or move course-specific material (video, Canvas, instructor URLs) to a separate course-maintained page the site merely links to? (Recommended: separate; it directly addresses the "overwhelming" complaint.)
11. **Gallery seeds**: approve the candidate list (expanded shop, adventure final, sophisticated_demo rework, `secret_examples` apps pending student permission, plus up to two purpose-built apps) and confirm permission/licensing for student work.
12. **Dormant themes**: re-enable `darkfairy`/`matcha` (then document) or leave dormant (then exclude from catalog)?
13. **AA scope**: does the WCAG 2.2 AA release requirement extend into the *content of compiled example apps*, or to the docs shell + demo controls with app-content issues tracked upstream?
14. **Versioning**: single rolling docs version for the beta, or versioned docs (mike) from the start? (Recommended: rolling until v2 stable.)
15. **Search scope**: should Teach/Dev pages be excluded from the default student search index?
16. **Hosting layout**: gallery apps on the same GH Pages site under `/gallery/…` (recommended, same-origin simplicity) or a separate deployment?

## 16. Explicitly outside the first release

- Localization/translation of any docs content.
- Community example/gallery submission workflows.
- Versioned documentation archives (unless Q14 decides otherwise).
- Analytics-driven error-index expansion (needs post-launch data).
- The commented-out debugger panels (coverage, test wizard) — documented only if/when they ship [R].
- A standalone student-facing REPL/playground app outside the docs (the `js/playground/` harness remains a dev tool [R]).
- Docstring-coverage completion of `src/` internals (owned by `DOCUMENTATION_PLAN.md`, not this plan; `/dev/api/` quality rises with it).
- Skulpt-engine documentation (Pyodide is the documented engine; Skulpt mentioned only as a CLI value).

## 17. Acceptance criteria

Release is acceptable when all of the following hold:

1. **Structure**: every §5 P0 and P1 row exists at its proposed URL with its listed status executed; nav matches §4; zero references to `docsrc/` or `ComponentDocs/`; all §8 redirects live.
2. **Coverage**: the coverage gate reports 100% of `drafter.__all__` either documented on a primary reference page or on the reasoned exclusion list; every component in §5.6 has a page (or family-page anchor) with all CRT sections; every L1/L2 concept has ≥2 runnable examples reachable from the Examples index.
3. **Executability**: 100% of runnable fences compile and execute green in CI; all in-page Drafter assertions pass; all error-entry repros produce their documented error text (or carry a recorded browser-only exemption per Q7).
4. **Templates**: the template linter reports zero missing required sections on P0/P1 pages.
5. **Links**: zero broken internal links; external links checked within the last release cycle; zero images without alt text.
6. **Accessibility**: automated scans (axe/pa11y) show zero serious/critical violations across the template × zone × scheme matrix; the five key flows pass a manual WCAG 2.2 AA audit; keyboard-only completion of: navigate to a component page, run a demo, edit and re-run a demo, read an error entry, search.
7. **Deployment guide**: a tester matching the audience profile completes prepare → publish → verify on a fresh repository using only the new pages, without assistance; the generic pages contain no course-specific terms.
8. **Errors**: paste-searching each seeded error's exact technical text returns its entry as the first result; explainer-parity report shows every curated friendly message mapped or excluded.
9. **Zones**: Teach and Dev render with their distinct schemes and banners; student pages contain no unmarked links into Teach/Dev body content.
10. **Behavioral validation**: the Phase J study is complete with results reported for time-to-first-success, task completion, navigation efficiency, error recovery, and transfer — separated from satisfaction measures — and no red-flag finding is left without a follow-up item in the backlog.
11. **Maintenance**: the docs-guide runbook exists; all five CI gates are required checks; adding a fake export in a test branch demonstrably fails gate 2.



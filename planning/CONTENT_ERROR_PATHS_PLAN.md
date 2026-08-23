# Content Error Paths Plan

Improving error messages for failures inside nested page content.

**Status (2026-08-23): IMPLEMENTED** (the recommended design, sections 1–4).
Notes from implementation:

- Indices use Python's 0-based convention ("row index 0", "column index 1"),
  matching the testing assertions' `index '0'` phrasing — not the 1-based
  ordinals in the mock below.
- `RenderPlan` also gained `children_are_content` (with a
  `Component.CHILDREN_ARE_CONTENT` class var, default True) to distinguish
  user-written child positions from generated structure; the renderer records
  the former as visible `index` steps and the latter as internal `child` steps.
- Labeled so far: `Table` (rows/columns/header row, incl. dataclass rows),
  `NumberedList`/`BulletedList` (items), `DefinitionList` (terms/definitions).
- Tests in `tests/test_content_error_paths.py`.
- Options D (error boundaries) and E (construction-site capture, behind a
  debug flag per user decision) remain future work.

## The problem

When rendering fails deep inside page content, students currently see something like:

> **Type Mismatch**
> Your code tried to use a value in a way that does not work for its type (for example, mixing text and numbers).
>
> `payload.rendering_failed: Payload rendering failed for URL index: Unsupported page content type: <class 'dict'>`
> `At ['[1]', 'table', '[1]', 'tbody', '[0]', 'tr', '[1]', 'td', '[0]']`

Five distinct things go wrong at once:

1. **The path is in the wrong vocabulary.** `component_stack`
   (`src/drafter/payloads/renderer.py`) records the *rendered HTML plan tree* —
   `table`, `tbody`, `tr`, `td`, plus raw `[N]` index strings. The student wrote
   `Table([[...], [...]])`; they never wrote `tbody` and cannot map `'[1]', 'tbody',
   '[0]'` back to "row 1, column 2 of my Table".
2. **Wrong classification.** The renderer raises a plain `TypeError`, so the
   central explainer (`drafter/data/error_explainer.py`, precedence tier 4:
   `EXCEPTION_EXPLANATIONS`) serves the generic "Type Mismatch" title and steps
   about argument counts and mixing text/numbers — none of which describe the
   actual mistake ("this value can't be page content").
3. **Message nesting/noise.** The envelope id (`payload.rendering_failed`), the
   wrapper prefix (`Payload rendering failed for URL index:`), and the raw
   exception text are concatenated. "URL index" reads like "URL index number"
   rather than "the page named `index`".
4. **The offending value is invisible.** Only `<class 'dict'>` is shown — not the
   value's repr, not which supported types exist, not what to do instead.
5. **Friendly text is dropped when `plan()` fails.** When a component's `plan()`
   raises (renderer.py:136-143), the exception is wrapped in `RenderError`,
   which does not carry the inner exception's `friendly_*` attributes; the
   explainer reads attributes off the *outer* exception only, so a
   `StudentFacingError` raised inside a component loses its friendly tier.

### Failure modes to cover

- Unsupported value type in content — top-level (`Page(state, [..., some_dict])`)
  and nested (inside `Table` rows, `Div`, `BulletedList`, `Row`/`Column`, etc.).
  Common offenders: `None` (function forgot to return / no-return branch),
  `dict`, `tuple` (student wrote `("a", "b")` instead of a list), `set`,
  `datetime`, dataclass instances, functions/methods (forgot `()` or meant a
  `Link`/`Button` target), classes (forgot `()`).
- A component's `plan()` raising mid-render (bad attribute values, invalid
  arguments discovered late) — including `StudentFacingError`s that should
  survive the wrap.
- `payload.formatting_failed` (history-panel formatting), which shares the
  wrap-and-lose pattern in `client_server.py`.
- Verification failures already flow friendly text through
  (`possible_failure.friendly_*` in `verify_payload`); rendering should reach
  parity.

## Design options

### Option A — Polish the strings we already have

Keep `component_stack: list[str]` but push component class names instead of tag
names, and format the final message with a joiner ("inside Table → item 1 →
item 1") instead of printing the raw list repr. Add an `ID_EXPLANATIONS` entry
for `payload.rendering_failed`.

- **Pros:** Tiny diff; no new data structures; immediate improvement.
- **Cons:** Indices still count *plan children*, not the student's rows/cells
  (`tbody` hides one level, so "item 1" ≠ "row 1" reliably). Strings can't be
  filtered, truncated smartly, or rendered differently by the debug panel vs.
  the error page. Doesn't fix classification precision or the lost-friendly-text
  wrap. We'd redo this work when we want real quality.

### Option B — Structured render path, shared with the testing path renderer

Promote the path to structured data and share the vocabulary that
`drafter/testing/assertions.py` already has (`PathItem(kind, name)` +
`render_path`):

- Move `PathItem` and `render_path` into a neutral module, e.g.
  `drafter/data/paths.py` (testing and payloads both import it; neither should
  import the other).
- `Renderer.component_stack` becomes `list[PathItem]`. The renderer pushes:
  - `PathItem("component", "Table")` when entering a `Component` (it knows
    `type(component).__name__` — no per-component work needed);
  - `PathItem("index", "2")` for list/children/fragment positions;
  - `PathItem("tag", "tbody")` for plan tags, marked *internal*.
- `RenderPlan` gains an optional `semantic_label: str | None`. A component that
  expands into structural HTML labels the plans it builds — `Table` labels each
  `tr` plan `"row 2"` and each `td` plan `"column 3"`; `BulletedList` labels
  `li` plans `"item 4"`. Unlabeled tags stay internal.
- The student-facing phrase renders only `component` frames, `semantic_label`s,
  and the indices between components: *"in the Page's content, item 2 (a Table),
  row 1, column 2"*. The full stack (tags included) still goes to `details` /
  the debug panel for instructor-level debugging.

- **Pros:** One path vocabulary across testing and rendering (assertion
  messages and render errors phrase locations the same way — good for docs and
  student habit-building). Precise student-level locations where components
  opt in; graceful generic fallback ("item N of the Div") where they don't.
  Structured data lets the debug panel highlight the failing node later.
- **Cons:** Touches `RenderPlan` and every structural component that wants good
  labels (Table, lists, layout containers — a bounded, incremental list).
  Slight ongoing discipline: new structural components should set labels.
  `render_path`'s current phrasing kinds (`keys`, `attributes`, …) are
  testing-specific; the shared module needs a superset without breaking
  existing assertion messages (existing tests pin those strings).

### Option C — Pre-render content validation walk

Before rendering, walk the *original* content tree (`Page.content`, component
constructor arguments) checking for unsupported types, and raise a
`StudentFacingError` phrased entirely in terms of what the student wrote —
before any HTML expansion exists.

- **Pros:** The best possible wording for the type-error case ("The 2nd thing in
  your Page's content is a Table; its row 1, column 2 holds a dictionary…") —
  no HTML vocabulary anywhere. Errors surface even for content that renders
  lazily. Could also run at `Page(...)` construction time, failing at the
  student's own line with a natural traceback.
- **Cons:** Duplicates traversal knowledge — the walker must know how every
  container component stores children (`Table.rows`, `Div.content`, …), and it
  will drift from `plan()` reality unless components declare their children
  (another protocol). Cannot catch errors that only materialize inside
  `plan()` (dynamic/computed content), so the render-time path is still needed
  as backstop — two systems to keep honest. Validation-at-construction changes
  when errors fire (a `Page` built but never returned would now raise), which
  is a behavior change tests and examples would feel.

### Option D — Soft-fail placeholder rendering (error boundaries)

Instead of aborting the render, drop an inline error box at the failing spot
(the `Renderer` already accumulates `self.errors`), render the rest of the
page, and highlight the broken node in situ — React-error-boundary style.

- **Pros:** Pedagogically the strongest "show, don't tell": the error appears
  *where the bad value would have appeared*, no path phrase needed. The rest of
  the page stays inspectable.
- **Cons:** Changes semantics: a page "renders" while broken, so
  `verify_payload`, tests, and grading flows must all learn that
  pages-with-embedded-errors are failures, or students ship broken pages
  without noticing. Risk of the error box scrolling out of view. Interacts
  with layout (a placeholder inside a `td` vs. inside `collapse_whitespace`
  runs). Significantly more machinery (styling, escaping, error-box component,
  status propagation). Better as a later layer on top of B than a replacement
  for a good message.

### Option E — Construction-site capture (file/line)

Record where each component was constructed (walk the stack in
`Component.__init__`, debug mode only) so errors can say "the `Table(...)`
created at `my_site.py:12`".

- **Pros:** The single most actionable pointer for a student — their own file
  and line, clickable in the editor.
- **Cons:** Per-instantiation overhead on every component (stack inspection is
  not free, and pages can build hundreds of components); needs gating to
  debug/dev mode; frame inspection behaves differently under Pyodide; the
  captured site can be misleading for components built in helper functions
  (points at the helper, not the call). Also orthogonal: even with a file/line
  you still want the in-structure path for values nested inside one big
  literal. Worth doing later as an additive field, not the core mechanism.

## Tradeoffs at a glance

| | A: polish strings | B: structured path | C: pre-render walk | D: error boundary | E: file/line capture |
|---|---|---|---|---|---|
| Student-level wording | partial | good (great where labeled) | best (for type errors) | n/a (visual) | best (source pointer) |
| Covers `plan()`-time failures | yes | yes | no | yes | yes |
| New protocols/machinery | none | `semantic_label` + shared paths module | child-declaration protocol | error-box + status plumbing | debug-mode capture |
| Risk of drift/dual-maintenance | low | low | **high** (walker vs. plan) | medium | low |
| Behavior changes | none | none | error timing moves | page renders while broken | perf in hot path |
| Reusable by debug panel / tooling | no | yes (structured) | partly | yes | yes |
| Effort | S | M | M–L | L | M |

## Recommended design: B as the spine, plus targeted raise sites

Option B, combined with fixing the classification and wrapping problems at the
raise sites. C, D, and E become future layers that all *consume* B's structured
path rather than competing with it. Concretely:

### 1. Shared path module — `drafter/data/paths.py`

Move `PathItem` and `render_path` out of `testing/assertions.py` (re-export
from `assertions` for compatibility). Extend the kind vocabulary with
`component`, `tag` (internal), and `label`. Add:

- `render_student_path(path)` — components + labels + interleaving indices
  only, phrased like assertion paths;
- `render_debug_path(path)` — everything, for `details`/logs/debug panel.

### 2. Renderer changes — `payloads/renderer.py`

- `component_stack: list[PathItem]`, pushed as described in Option B.
- `RenderPlan.semantic_label: str | None = None`; the renderer pushes
  `PathItem("label", plan.semantic_label)` when set, else the internal tag
  frame.
- The unsupported-type raise becomes a `StudentFacingError` built by a helper,
  e.g. `unsupported_content_error(value, path)` in a small new
  `payloads/content_errors.py`, with **type-targeted advice**:

  | Offending value | Extra advice |
  |---|---|
  | `None` | "This often means a function forgot to `return` something, or an `if` branch has no return. Check that every path in your route returns content." |
  | `dict` | "Dictionaries can't be shown directly. Convert it with `str(...)`, or display it as a `Table`." |
  | `tuple` / `set` | "Use a list `[...]` instead of a tuple/set for page content." |
  | function/method | "You used a function itself as content. If you meant to call it, add `(...)`. If you meant a link, use `Link('text', the_function)` or a `Button`." |
  | class | "You used the class itself — did you forget the parentheses to create one?" |
  | anything else | "Pages can show text, numbers, booleans, images, and Drafter components. To display this value as text, wrap it in `str(...)`." |

  The technical message keeps the type and a truncated `repr` of the value
  (`repr(value)` capped ~80 chars, escaped); the friendly message uses the
  student path phrase; `friendly_steps` carry the targeted advice.
- The `plan()` failure wrap: `RenderError` copies `friendly_title` /
  `friendly_message` / `friendly_steps` from the caught exception when present
  (or `RenderError` itself becomes a `StudentFacingError` subclass), so a
  component's own friendly text survives to the explainer. The wrap message
  uses the student path phrase, with the debug path in details.

### 3. Envelope/explainer changes

- `ID_EXPLANATIONS` gains `payload.rendering_failed` (and
  `payload.formatting_failed`): title "Page Content Problem", a message
  explaining that Drafter couldn't turn the returned content into a page, and
  generic steps — used only when the exception carried nothing (tier 1 still
  wins, so the targeted `StudentFacingError` text takes precedence).
- `client_server.render_payload`'s wrapper message drops the confusing
  `for URL index:` phrasing in favor of `for the page '/index'` (quote the
  URL), and stops duplicating the exception text the envelope already carries
  in `details`.

### 4. Component labels (incremental, prioritized)

First wave: `Table` (rows/columns — the motivating case), `BulletedList` /
`NumberedList` (items), `Row`/`Column`/`Div` (positions), form containers.
Anything unlabeled degrades to "item N" — acceptable.

### 5. What the final error should look like

> **Page Content Problem**
> Your page content includes a value Drafter doesn't know how to display: a
> dictionary (`{'name': 'Ada', 'kind': 'corgi'}`).
> It is in the 2nd item of your Page's content — a **Table** — at **row 1,
> column 2**.
>
> Things to try:
> - Dictionaries can't be shown directly. Convert it with `str(...)`, or display it as a `Table`.
> - Pages can show text, numbers, booleans, images, and Drafter components.
>
> *Technical details:* `Unsupported page content type dict at Page content
> index 1 → Table → row 1 → column 2 (table > tbody[0] > tr[0] > td[1])` —
> `payload.rendering_failed`, URL `/index`.

### Testing

- Unit tests for `paths.py` phrase rendering (student + debug variants) —
  including that existing assertion-path strings are unchanged.
- Renderer tests: nested unsupported values under Table/lists/Div produce the
  expected student phrase; `plan()`-raised `StudentFacingError` keeps its
  friendly text through the wrap; `None`/`tuple`/function/class advice tables.
- Event-contract check: `ErrorDetails` shape unchanged (friendly fields
  already exist), so no envelope schema change expected.

### Future extensions (explicitly out of scope now)

- **Option D** (inline error boundary in debug mode) rendering the same
  `StudentFacingError` in place, once payload-with-errors status semantics are
  designed.
- **Option E** (debug-mode construction-site capture) adding a `file:line` to
  the friendly message.
- Debug-panel integration: use the structured path to highlight the failing
  node in the payload tree view.

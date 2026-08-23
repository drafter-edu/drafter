# Two-Tier Error Messages Plan

Goal: every student-visible error shows **two messages** — a technically
concise, accurate one, and a student-friendly explanation in simpler terms —
generated centrally rather than heuristically at each rendering surface.

> **Status (2026-07-26): ALL PHASES IMPLEMENTED.**
> Contract fields, the central explainer (`src/drafter/data/error_explainer.py`),
> producer wiring, and all renderer updates are shipped and tested.
> `StudentFacingError` migration is complete across every §1.6 cluster
> (validation, attributes, text, forms, audio, images, links, layout,
> page_content, persistence, map, plotting, camera, dates, fragment — only
> `raise ValueError` sites; TypeError/ImportError sites intentionally kept
> their types). The "trim URL-wrapper prefixes out of message" idea in §2.4
> was deliberately NOT done (kept technical messages stable to avoid churn).
>
> **Additions beyond the original plan (same date):**
> - `ErrorDetails.data: dict` — structured, JSON-safe details, sanitized at
>   construction by `json_safe()` (handles `to_json()` objects, dataclasses,
>   nesting; falls back to repr). In `to_json()` and mirrored as optional
>   `data` in `ErrorDetailsJson`.
> - Route call capture: `ClientServer._route_call_reprs` remembers the
>   best-known generated call per in-flight request — an approximation from
>   raw request values once the route resolves, upgraded to the exact bound
>   representation after `prepare_arguments` succeeds — and
>   `make_visit_error` attaches it to every visit-failure envelope as
>   `data["route_call"]` / `data["route_call_exact"]`, plus
>   `data["request"]` (structured request) automatically.
> - Error page technical table: dedicated "Route Call" row (with an
>   "approximate" note when not exact), each `data` key rendered as its own
>   row via a recursive nested renderer (`_render_data_value`: dict → nested
>   table, list → bullets, scalars → inline code/preformatted), empty
>   Details row omitted, Traceback moved last. Producers no longer stuff
>   `repr(request)`/`repr(payload)` into `details`; those now travel in
>   `data` and render as structure.
> - Refinements: the approximate route call excludes framework `--` keys
>   (e.g. `--submit-button`); step strings may mark code in backticks,
>   rendered as inline code by both the Python page (`_render_step`) and
>   the JS root overlay (`appendStepContent`); the explainer produces a
>   third tier, `friendly_title` (per-id/per-exception-type/per-category
>   page titles — e.g. `request.argument_parsing_failed` → "Problem With
>   the Route's Arguments", NameError → "Unknown Name"), used as the error
>   page heading unless `error_page_title` overrides it; nested data values
>   (like the request) start collapsed in a `<details>` ("Show details").

## Part 1: Inventory of student-facing error message generation

### 1.1 The canonical contract (spine of everything)

- `ErrorDetails` dataclass — `src/drafter/data/errors.py:110`. Fields already
  distinguish `message` ("human-safe") from `details` ("developer-focused"),
  but in practice `message` is technical (e.g. `Error while processing request
  for URL '/index': division by zero`). Subclasses `Exception`; `to_json()`
  (`errors.py:149`) is the wire shape shared with JS.
- `envelope_from_exception` — `data/errors.py:174`. The primary point where a
  raw exception (including student-code exceptions) becomes a student-facing
  message (`message` defaults to `str(exception)`); formats the traceback.
- JS mirror: `ErrorDetailsJson` — `js/src/debug/telemetry/errors.ts:40`.

### 1.2 Visit-lifecycle errors (all funnel to the error page)

`ClientServer.make_visit_error` — `src/drafter/client_server/client_server.py:299`
builds the envelope; `do_visit` catches it (`:711`); `make_error_response`
(`:866`) dispatches to the `--error` route. Error ids and message templates:

| client_server.py | id | trigger |
|---|---|---|
| `:369` | `request.route_not_found` | 404 |
| `:449` | `request.argument_parsing_failed` | parameter pipeline failure |
| `:461` | `request.route_execution_failed` | **student route function raised** (main path) |
| `:487/:501/:511` | `payload.verification_failed` | bad payload / verify raised |
| `:543` | `payload.rendering_failed` | component render raised |
| `:578` | `payload.formatting_failed` | payload.format raised |
| `:611` | `payload.state_verification_failed` | state history verify |
| `:629` | `payload.state_update_failed` | state.update raised |
| `:819/:854` | `payload.target/message_retrieval_failed` | payload accessors raised |
| `:730` | `system.response_creation_failed` | response construction |
| `:900` | `system.error_page_failed` | error route itself threw → `SimpleErrorPage` fallback (`payloads/kinds/error_page.py:23`, "System Error: {message}") |

Site-level fallback: `format_simple_site_error` (`client_server.py:967`) and
hard-coded "System Error (Fallback Level 2)" HTML (`:981–994`).

### 1.3 The error page renderer (Python surface)

`default_error` — `src/drafter/router/defaults/error.py:258`:
- Friendly summary: `_build_friendly_summary` (`error.py:191`) — keyed on
  `error.id`/`error.category`, marked `# TODO: Expand on these a bit more`.
- Technical line: `PreformattedText(f"{error.id}: {error.message}")` (`:285`).
- Fix steps: `_build_fix_steps` (`error.py:208`) — **substring-matches**
  "SyntaxError"/"NameError"/"TypeError"/"IndexError"/"KeyError" against
  message+details+traceback text.
- Technical details table gated by `error_page_show_details` (`:299`);
  styled traceback with student-frame detection (`_render_traceback` `:165`,
  `_INTERNAL_PATH_MARKERS` `:34`).
- Config overrides: `error_page_title`, `error_page_message`,
  `error_page_show_details`.

### 1.4 JS system-error surface (root overlay / dialog)

`reportSystemError` — `js/src/bridge/engine.ts:300` (single entry point);
presentation matrix `resolvePresentation` (`:148`).
- Root error page: `renderSystemErrorInRoot` (`:226`) — "Something Went
  Wrong", lead + steps + technical `<pre>`.
- Friendly builders (duplicating the Python heuristics): `buildStudentLead`
  (`:180`, keyed on id substrings `pyodide_setup`/`package_`/
  `student_code_failed` and category), `buildStudentSteps` (`:196`,
  substring-matching SyntaxError/NameError), `DEFAULT_SUGGESTION` (`:37`).
- Dialog path: `formatSystemErrorMessage` (`:165`).
- Callers: `js/src/pyodide.index.tsx` (`:791` instance configure, `:814` code
  write, `:841` **student code failed** — main Pyodide path, plus pyodide/
  package setup sites), `js/src/skulpt_bridge/skulpt-tools.ts:154`.

### 1.5 Parameter pipeline (already two-tier — the precedent)

- `RouteDiagnostic` — `src/drafter/router/parameters/diagnostics.py:30`:
  `message` (student-facing description) + `hint` (student-facing fix
  suggestion) + `severity`/`code`/`parameter`/`source`. Five `DiagCode`s.
- `format_diagnostic` (`:55`) **flattens** message+hint into one string;
  `ParameterBindingError` (`:71`) joins all lines into `str(e)`, which then
  becomes the technical message of `request.argument_parsing_failed` —
  the structure is lost before reaching the error page.
- Warning diagnostics become `request.{code}` warning envelopes at
  `router/routes.py:274` (problems panel, page-scoped via request_id).

### 1.6 Component/library raise sites (surface via route execution/rendering)

Plain `ValueError`/`TypeError` raised while student code runs; `str(e)` ends
up embedded in the lifecycle message. Notable clusters:
- `components/utilities/validation.py` — `BASE_PARAMETER_ERROR` (`:7`),
  `BASE_VALUE_ERROR` (`:16`), raises at `:37–:91`.
- `components/utilities/attributes.py:247` — invalid enum attribute value.
- `components/audio.py` (largest cluster: `_bad_note_message` + ~20 raises),
  `data/images.py` (~14 raises), `components/forms.py:275`, `text.py:139`,
  `links.py`, `layout.py`, `page_content.py`, `persistence.py`, `map.py`,
  `plotting.py`, `camera.py`, `helpers/dates.py:46`,
  `payloads/kinds/fragment.py`, `styling/generics.py`.
- `payloads/renderer.py`: `RenderError` (`:22`), raise at `:136` with
  component stack; `TypeError` for unsupported content (`:197`).
- Theme suggestion: `site/site.py:151`
  (`theme_system.suggest_mistake(...)` — already friendly-ish).

### 1.7 Bridge errors (surface via JS root/dialog + telemetry)

`src/drafter/bridge/error_handling.py`: `report_bridge_error` (`:35`),
`report_bridge_warning` (`:114`), `raise_bridge_system_error` (`:149`).
Call sites in `bridge/runtime.py:359`, `navigation.py:211`,
`client_bridge.py:262`, `events.py:923/:1018`, `snapshot.py:248`,
`site_renderer.py:169`.

### 1.8 Problems panel (global vs page)

Transport: `Response.errors/warnings` (`data/response.py:49–50`), warnings
captured per-request in `do_visit` (`client_server.py:679–693`). JS:
`DebugPanel.trackProblem` (`js/src/debug/index.tsx:686`),
`CurrentPanel.renderProblem` (`js/src/debug/panels/current.tsx:149`) shows
`envelope.message` with collapsible `envelope.details`. Global iff
`context.request_id == null` (`index.tsx:700`). Warning generators:
`router/routes.py:274` (page), `history/state.py:77/:112` (global),
`report_bridge_warning`.

### 1.9 Adjacent but out of scope for the error page

- Dev-server debug log (`src/drafter/app/error_log.py`,
  `js/src/debug/error_reporter.ts`) — diagnostics capture, not student UI;
  will transparently benefit from richer envelopes.
- Testing framework messages (`testing/reporting.py:205–207`, rendered by
  `js/src/debug/panels/testing.tsx:146`) — already have a "one
  student-friendly sentence" summary design; not part of the error page.
- Config/build/docs errors that can't occur during a request.

### 1.10 Key problems with the current design

1. **Friendly text is computed at render time, twice** — duplicated
   heuristics in `error.py` (Python page) and `engine.ts` (JS overlay), which
   will drift.
2. **Classification by substring matching** on flattened text
   ("TypeError" in combined) instead of by exception type — fragile (e.g. a
   student string containing "KeyError" misclassifies).
3. **Structure is destroyed early**: `ParameterBindingError` flattens
   message+hint; component `ValueError`s get wrapped in
   "Error while processing request for URL ...: {e}", burying the useful part.
4. `ErrorDetails.message` conflates "technical line" and "human-safe line" —
   there is no field for the student-friendly tier, so renderers improvise.

## Part 2: Target architecture

### 2.1 Principle

The envelope is the single source of truth for **both tiers**. Renderers
become dumb: they display fields, they don't infer.

- **Technical tier** = `id` + `message` (+ `details`/`traceback`). `message`
  stays concise and accurate; `str(exception)` remains untouched so logs and
  tracebacks stay truthful.
- **Friendly tier** = new envelope fields, computed **once at envelope
  creation time** (where the original exception object is still in hand, so
  classification is by `type(exception)`, not substrings).

### 2.2 Contract change — `ErrorDetails` (`data/errors.py`)

Add (all additive, backward-compatible defaults):

```python
friendly_message: str = ""        # one plain-language sentence
friendly_steps: tuple[str, ...] = ()  # concrete "what to try next" bullets
```

- Include both in `to_json()`.
- Mirror in `ErrorDetailsJson` (`js/src/debug/telemetry/errors.ts`) as
  optional fields, and in `normalizeEnvelope`
  (`js/src/debug/error_reporter.ts:41`).
- Update event-contract tests (known gotcha: detail shapes are asserted).

Decision: fields on the envelope, not a nested `student:` object — flat
fields match the existing envelope style, keep the wire diff minimal, and the
"empty string/tuple means not provided" convention lets renderers fall back.

### 2.3 New central explainer — `src/drafter/data/error_explainer.py`

One module owning all friendly-text generation:

```python
def explain(
    exception: BaseException | None,
    error_id: str,
    category: str,
    diagnostics: Sequence[RouteDiagnostic] = (),
) -> tuple[str, tuple[str, ...]]:  # (friendly_message, friendly_steps)
```

Resolution order (first match wins):
1. **Exception-carried text** — if the exception is a `StudentFacingError`
   (see 2.5) its `friendly`/`steps` win.
2. **Structured diagnostics** — `ParameterBindingError.diagnostics` map
   directly: friendly_message summarizes ("Drafter couldn't match the
   information sent to your `{route}` function's parameters."), each
   diagnostic's `message`+`hint` becomes one step. No flattening.
3. **Exception-type table** — `{SyntaxError, NameError, TypeError,
   IndexError, KeyError, AttributeError, ValueError, ZeroDivisionError,
   ImportError/ModuleNotFoundError, RecursionError, ...} → (sentence, steps)`,
   ported from `_build_fix_steps` but keyed on `type(exception).__mro__`
   instead of substrings. Where cheap, extract specifics (e.g. `NameError
   .name`, `AttributeError.name/obj`) into the sentence.
4. **Error-id/category table** — port `_build_friendly_summary` cases
   (`request.route_not_found`, per-category sentences) and the JS
   `buildStudentLead` cases (`runtime.pyodide_setup_*`, `runtime.package_*`,
   `runtime.student_code_failed`).
5. **Generic fallback** — current 5-step generic advice.

Registry-style tables (dicts, not if-chains) so future error ids/exception
types are one-line additions and unit-testable in isolation.

### 2.4 Wire the explainer into envelope constructors

- `envelope_from_exception` (`data/errors.py:174`): call `explain(...)` and
  populate the new fields (allow explicit override kwargs).
- `make_visit_error` (`client_server.py:299`): pass the caught exception
  through (it already has it in every call site) so classification sees the
  real exception, not the wrapped message. Also: keep `message` for these
  wrappers but consider trimming the "Error while processing request for URL
  ... :" prefix into `details`, leaving `message` = the actual exception line
  (`{type}: {str(e)}`) — that is the "technically concise and accurate"
  requirement.
- `report_bridge_error` / `raise_bridge_system_error`
  (`bridge/error_handling.py`): same treatment.
- `routes.py:274` warning diagnostics: populate friendly fields from the
  diagnostic's message/hint pair instead of flattening.

### 2.5 Optional authoring API — `StudentFacingError`

New exception in `data/errors.py` (or `data/exceptions.py`):

```python
class StudentFacingError(ValueError):
    def __init__(self, message: str, *, friendly: str = "", steps: Sequence[str] = ()):
```

`str(e)` stays the technical message; `friendly`/`steps` ride along for the
explainer's rule 1. Then migrate high-value component raise sites
incrementally (no flag day — plain `ValueError`s keep working via rule 3):
- `components/utilities/validation.py` (BASE_PARAMETER_ERROR /
  BASE_VALUE_ERROR sites)
- `components/utilities/attributes.py:247`
- `components/audio.py` (`_bad_note_message` cluster), `data/images.py`,
  `components/forms.py:275`, then the remaining component sites from §1.6.
- `payloads/renderer.py:136` — `RenderError` gains the same fields; friendly
  text names the component and page position from `component_stack`.

### 2.6 Renderer changes (become consumers, not generators)

**Python error page** (`router/defaults/error.py`):
- `default_error` uses `error.friendly_message or _build_friendly_summary(error)`
  and `error.friendly_steps or _build_fix_steps(error)` during migration;
  once all envelope producers populate the fields, the local heuristics
  shrink to the fallback table (or move wholesale into the explainer and get
  deleted here).
- Page layout: friendly sentence first (as now), technical line
  `{id}: {message}` stays, steps section renders `friendly_steps`.
- `error_page_message` config override keeps precedence over
  `friendly_message`.

**JS surfaces** (`js/src/bridge/engine.ts`):
- `SystemErrorReport` gains optional `friendlyMessage`/`friendlySteps`;
  `buildEnvelope` copies them into the envelope fields.
- `renderSystemErrorInRoot` / `formatSystemErrorMessage` prefer envelope
  fields; `buildStudentLead`/`buildStudentSteps` remain only as fallback for
  **JS-origin** errors (pyodide setup, package loading) that never pass
  through Python — that duplication is inherent but shrinks to the handful of
  JS-only error ids.
- Python-origin errors surfaced via telemetry/bridge (e.g.
  `runtime.student_code_failed` payloads that carry a Python envelope) should
  pass the Python-computed friendly fields through rather than re-deriving.

**Problems panel** (`js/src/debug/panels/current.tsx:149`):
- `renderProblem` shows `friendly_message` when present (technical
  `message` moves next to `details` in the collapsible), falling back to
  `message` as today. Check i18n-parity tests when touching panel strings.

**Fallback layers**: `SimpleErrorPage` (`payloads/kinds/error_page.py:23`)
and the Level-2 HTML fallback (`client_server.py:981`) get one static
friendly sentence each ("Drafter itself hit a problem while showing your
error...") — no explainer dependency, these must stay bulletproof.

### 2.7 Explicit non-goals

- No LLM/CS50-duck style explanation generation; static tables only.
- No change to `str(exception)`, tracebacks, or the debug log format beyond
  the additive envelope fields.
- Testing-panel messages keep their existing summary design.

## Part 3: Implementation phases

1. **Contract**: add `friendly_message`/`friendly_steps` to `ErrorDetails`,
   `to_json`, `ErrorDetailsJson`, `normalizeEnvelope`; update event-contract
   tests. (Small, unblocks everything.)
2. **Explainer module** + unit tests: port `_build_friendly_summary`,
   `_build_fix_steps`, `buildStudentLead` content into type/id-keyed tables;
   add diagnostics mapping. This is also the moment to expand/improve the
   actual wording (the existing `# TODO: Expand on these a bit more`).
3. **Producers**: wire explainer into `envelope_from_exception`,
   `make_visit_error` (thread the exception object through), bridge error
   helpers, and route warning diagnostics. Trim the URL-wrapper prefixes out
   of `message` into `details`.
4. **Renderers**: Python error page, JS root/dialog, problems panel switch to
   envelope fields with fallback; static fallback pages get their sentence.
5. **Raise-site migration** (incremental, low risk): `StudentFacingError` +
   the §1.6 clusters, starting with validation.py, attributes.py, audio.py,
   images.py, forms.py.
6. **Tests/docs**: explainer unit tests per exception type and error id;
   e2e check that a student `NameError` shows both tiers on the error page;
   i18n-parity and event-contract suites; document the two-tier convention
   for future error authors (where to add table entries, when to use
   `StudentFacingError`).

Phases 1–4 deliver the two-tier system everywhere; 5 improves message
quality site-by-site and can be spread over time.

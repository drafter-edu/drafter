# AGENTS.md

Repository-wide instructions for AI coding agents working on Drafter v2. These instructions apply to the entire repository unless a more specific `AGENTS.md` exists in a subdirectory.

## Project priorities

Drafter is a student-facing, full-stack Python web-development library. Optimize changes in this order:

1. Correct behavior across the supported execution environments.
2. A simple, predictable, and well-documented student-facing API.
3. Regression protection through focused tests.
4. Maintainable code with clear boundaries and explicit types.
5. Small, reviewable diffs rather than speculative refactors.

Do not trade correctness or API clarity for cleverness, abstraction, or reduced line count.

## Sources of truth

- The implementation is authoritative. If `ARCHITECTURE.md` disagrees with the code, follow the code and update the architecture document when the change is architectural.
- Use `pyproject.toml`, `Justfile`, `js/package.json`, and `.github/workflows/test_and_lint.yml` for current tooling and validation commands.
- Follow `CONTRIBUTING.md` for public documentation and docstring conventions.
- Follow `js/TESTING.md` for JavaScript and browser-runtime test placement and execution.
- Do not invent APIs, paths, commands, or compatibility promises. Inspect the repository first.

## Environment and setup

Python development uses `uv`; JavaScript development uses npm.

```bash
uv sync --all-extras
cd js && npm ci
```

Use `uv run ...` for Python tools and commands. CI tests Python 3.10 through 3.14 and uses Node.js 22. Code must remain valid on Python 3.10 unless the project explicitly changes its minimum version.

Useful entry points:

```bash
just --list
just check
just test
just build
```

`just validate` runs formatting and linting with automatic fixes before tests. It is useful during development, but final verification must include non-mutating checks so that uncommitted formatter or lint changes are not hidden.

## Repository map

- `src/drafter/`: Python package, including routing, components, payloads, client-server logic, browser bridge, app server, builder, site rendering, and configuration.
- `tests/`: Python pytest suite.
- `js/src/`: TypeScript client, runtime adapters, browser integration, custom elements, and debug UI.
- `js/src/__tests__/`: JavaScript unit, component, Pyodide, and Skulpt tests.
- `js/e2e/`: Playwright browser tests.
- `js/dist/`: generated JavaScript assets consumed by the Python package, docs, tests, and wheel build.
- `examples/`: runnable, student-facing examples and behavioral demonstrations.
- `docs/` and `docsrc/`: documentation sources and generated/example inputs.
- `tools/`: repository maintenance and validation scripts.

## Required working method

For every nontrivial change:

1. Read the affected implementation, its callers, neighboring tests, and relevant documentation before editing.
2. Identify which runtime boundaries are involved: CPython host, Pyodide client, Skulpt client, TypeScript bridge, static builder, or development server.
3. Make the smallest coherent change that fixes the problem or implements the request.
4. Add or update a regression test that fails before the fix and passes afterward whenever behavior changes.
5. Run targeted tests first, then the applicable broader checks listed below.
6. Review the final diff for accidental API changes, generated-file noise, stale docs, and unrelated edits.
7. Report what changed, exactly which commands ran, and any checks that could not run.

Do not silently broaden the scope. Explain any necessary adjacent change in the final summary.

## Architectural invariants

Preserve these constraints unless the task explicitly requires an architectural change:

- `start_server` dispatches among browser mode, static compile mode, and normal CPython app mode. A change in shared code may affect all three.
- Student application code executes once on the host and again in the browser. Do not assume that code reachable in the browser has normal CPython filesystem, process, networking, threading, or package availability.
- Pyodide is the default browser engine. Skulpt is legacy and effectively unmaintained: its Jest project (`npm run test:skulpt`) is known-failing and excluded from the validation baseline, so do not modify, run, or try to fix Skulpt code or tests (`js/src/skulpt_bridge/`, the Skulpt bundles, `precompile`, `update-skulpt`) unless a task explicitly targets Skulpt. Still avoid introducing CPython-only language or library behavior into shared runtime paths.
- Keep the `ClientBridge` focused on DOM interaction and transport. Put application, routing, state, validation, and response logic in the `ClientServer` or other Python-side domain modules.
- A `ResponsePayload` is the content to display; a `Response` carries system metadata. Error paths must still produce and send a `Response`.
- Preserve lazy initialization of the module-level main server and isolation between registered Drafter instances. Avoid mutable global state that can leak across embedded applications or tests.
- `DRAFTER_TAG_IDS` and the site templates in `src/drafter/site/site.py` are the source of truth for Drafter DOM identifiers. Do not scatter duplicate identifier literals or remove the established trailing `--` convention.
- Treat Python/TypeScript message shapes, runtime envelopes, event contracts, and telemetry fixtures as cross-language APIs. Update producers, consumers, fixtures, and tests together.
- `js/dist/` is required by compilation, documentation demos, Python tests that resolve assets, and packaging. Build it from source; do not hand-edit generated bundles.

When changing an invariant, update `ARCHITECTURE.md` and add tests at the boundary being changed.

## Python standards

- Use explicit type annotations for new and changed public or nontrivial internal code.
- Prefer precise domain types over `Any`, unstructured dictionaries, and unchecked casts.
- Do not add `# type: ignore`, `# noqa`, or broad lint exclusions unless the underlying issue cannot reasonably be fixed. Scope any suppression narrowly and explain why it is safe.
- Preserve Python 3.10-compatible syntax and standard-library usage.
- Keep public student-facing APIs straightforward. Prefer descriptive names, useful defaults, and actionable errors over highly generic abstractions.
- Avoid changing exported names, constructor signatures, route behavior, state conversion, rendering semantics, or error behavior without explicit need and regression coverage.
- Validate at system boundaries and raise specific exceptions with useful context. Do not catch broad exceptions merely to continue silently.
- Follow existing dataclass and immutability conventions in the affected subsystem.
- Avoid import-time side effects, eager global initialization, and circular-import workarounds that obscure architecture.
- Keep functions focused, but do not split simple logic into excessive layers.

### Python formatting, linting, and typing

```bash
uv run ruff format --check
uv run ruff check
uv run mypy --ignore-missing-imports --install-types --non-interactive --package drafter
uv run python tools/doc_drift.py
```

During implementation, format only affected paths when practical:

```bash
uv run ruff format path/to/file.py tests/path/to/test_file.py
uv run ruff check --fix path/to/file.py tests/path/to/test_file.py
```

Always run the repository-wide non-mutating checks before declaring a broad Python change complete.

## Documentation and docstrings

Public documentation is part of the product because the primary audience includes students.

- Use Google-style sections: `Args:`, `Returns:`, `Raises:`, `Yields:`, `Attributes:`, `Note:`, and `Example:`.
- Do not repeat annotation types in `Args:` entries.
- Document dataclass fields and public instance attributes in declaration order.
- Put a PEP 224-style string literal immediately after public top-level constants.
- Do not put TODOs in docstrings; docstrings describe current behavior.
- Do not use Sphinx roles. Use plain backticks or mkdocstrings cross-references.
- Document deliberate exceptions in `Raises:`.
- Add a short, realistic `Example:` for student-facing components, styling helpers, assertions, and payloads.
- Update docs and examples when public behavior changes. Examples should remain readable teaching material, not merely integration fixtures.

Build documentation through the project wrapper rather than invoking MkDocs directly:

```bash
just docs
# or
uv run drafter-docs build
```

Use `uv run drafter-docs build --api` when changing API-reference behavior or public docstrings.

## JavaScript and TypeScript standards

Run all JavaScript commands from `js/`.

- Preserve the ESM and TypeScript conventions already used in the directory.
- Match existing formatting and indentation in nearby files; tests currently use tab indentation.
- Keep DOM/browser concerns in the TypeScript layer and domain behavior in Python when the architecture already assigns it there.
- Mock at broker or browser-API boundaries rather than mocking deep implementation details.
- Do not use bare `npx jest`; npm scripts provide required ESM flags and project selection.
- Do not run Playwright from the repository root. Use the npm script from `js/` so the correct configuration, bundle, Python zip, package cache, and server are used.
- Place tests in `src/__tests__/pyodide/` only when they require a real interpreter. Pyodide test files must remain isolated in separate Jest processes because WASM memory is not reclaimed reliably.
- Update telemetry JSON fixtures and their provenance documentation together with the corresponding Python emitters.

JavaScript validation commands:

```bash
cd js
npm test
npm run test:integration
npm run test:e2e
npm run build
```

Choose the smallest applicable set during development, but run every tier affected by the change. (`npm run test:skulpt` exists but is legacy and known-failing; leave it out unless a task explicitly targets Skulpt.)

## Testing requirements by change type

### Python-only internal change

Run the nearest targeted pytest module, then:

```bash
uv run pytest --verbose --color=yes tests
just check
uv run python tools/doc_drift.py
```

If the tests or implementation resolve browser assets, run `just build-js` first.

### Public Python API, routing, rendering, state, payload, or configuration change

In addition to the Python checks:

- Add behavior and error-path tests.
- Run affected examples when practical.
- Run relevant Pyodide integration tests because shared Python code executes in the browser.
- Build docs when signatures, docstrings, examples, or student-visible behavior change.

### TypeScript unit or component change

```bash
cd js
npm test
npm run build
```

### Runtime adapter, bridge, event contract, persistence, or Python/JavaScript boundary change

```bash
cd js
npm test
npm run test:integration
npm run test:e2e
npm run build
```

Skulpt is legacy: skip `npm run test:skulpt` even for shared behavior unless the task explicitly targets Skulpt.

### Static builder, asset resolution, docs demo, or packaging change

```bash
just build-js
uv run pytest --verbose --color=yes tests
just docs
just build
```

Confirm that the built wheel contains the expected `drafter/assets/` JavaScript files.

### Broad or cross-cutting change

Run the CI-equivalent gates that apply:

```bash
just check
uv run python tools/doc_drift.py
just test
cd js && npm run test:e2e
just build
```

Do not claim that a change is fully validated when a relevant runtime tier was skipped.

## Test quality

- Test externally observable behavior, invariants, and boundary contracts rather than private implementation details.
- Add a focused regression test for every fixed bug.
- Cover success, malformed input, and deliberate error behavior where relevant.
- Keep tests deterministic and independent. Avoid real external network dependencies, wall-clock assumptions, race-prone sleeps, and order dependence.
- Do not weaken, delete, skip, or broaden assertions merely to make a failing suite pass.
- Do not place ordinary unit tests in expensive Pyodide or browser suites.
- A test documenting a known production bug should clearly state that it asserts current behavior; fixing the bug should require intentionally changing that test.
- Preserve multi-instance isolation and cleanup global registries, timers, DOM state, mocks, and runtime resources between tests.

## Generated files, dependencies, and lockfiles

- Do not hand-edit `js/dist/`, build outputs, coverage files, caches, or generated documentation.
- Rebuild generated assets only when their sources change or a validation/build command requires them.
- Do not modify `uv.lock` or `js/package-lock.json` unless dependencies change.
- Prefer existing dependencies and standard-library facilities. A new dependency requires a concrete benefit, compatibility review, and appropriate lockfile updates.
- Do not commit `.venv`, `node_modules`, `dist/` packaging outputs, test results, browser traces, or local configuration files unless the repository already tracks a specific generated artifact intentionally.

## Security and reliability

Drafter handles user-authored Python, form data, uploads, URLs, HTML, JavaScript, and browser events. Treat these as boundary inputs.

- Preserve escaping, sanitization, validation, and explicit raw-content APIs.
- Do not introduce implicit `eval`, `exec`, unsafe HTML insertion, path traversal, arbitrary file access, or unrestricted URL fetching.
- Preserve request provenance and parameter precedence when changing form or route binding.
- Avoid leaking state, event listeners, DOM nodes, timers, or resources across app instances and reloads.
- Do not log sensitive uploaded content or user state unnecessarily.
- Fail with actionable diagnostics rather than silent fallback when correctness is uncertain.

## Change discipline

Do not:

- Refactor unrelated code in the same patch.
- Reformat untouched files without a reason.
- Rename or reorganize public APIs opportunistically.
- Add speculative compatibility layers or unused abstractions.
- Duplicate logic that already has a clear owner.
- Silence failing checks without addressing their cause.
- Update changelogs, versions, or release metadata unless the task calls for it.

Prefer one clear implementation path with tests over several partially supported paths.

## Completion criteria

A change is complete only when:

- The requested behavior is implemented with a minimal coherent diff.
- Relevant regression tests exist and pass.
- Formatting, linting, typing, and doc-drift checks pass for affected Python code.
- Relevant JavaScript unit, integration, Skulpt, and browser tiers pass.
- Generated assets are rebuilt when required, never edited manually.
- Public docs, docstrings, architecture notes, and examples match the implemented behavior.
- Python 3.10 compatibility and cross-runtime constraints were considered.
- The final response lists changed files, validation commands, and any known limitations or unrun checks.

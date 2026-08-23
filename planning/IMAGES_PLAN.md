# Images as a First-Order Concept: Design & Migration Plan

Status: IMPLEMENTED (2026-07-25). Phases 1-6 are complete on this branch;
see §12 for the resolved open questions. Notable deviation: uploaded
`DrafterBinaryFile` values are described in the debug panel as ordinary
dataclasses whose `content` field uses the new `bytes` kind (with image
thumbnail), rather than a dedicated small-struct kind (§7.1).

Premise: Pillow is now a full, unconditional dependency of Drafter (it is
already in `pyproject.toml` dependencies and in the Pyodide system-package
load list). Skulpt compatibility is no longer a constraint. This plan makes
images a first-class data concept instead of a set of scattered PIL
special-cases.

---

## 1. Current state (audit summary)

Every subsystem re-implements "is this a PIL image? then base64-PNG it."
There is no shared image value type, no shared encoding helper, and no
preview protocol.

**Six independent PIL→base64-PNG implementations:**

| Site                                                             | Purpose                       |
| ---------------------------------------------------------------- | ----------------------------- |
| `src/drafter/components/images.py` `_handle_pil_image`           | Image component rendering     |
| `src/drafter/components/files.py` `_handle_pil_image`            | Download component            |
| `src/drafter/components/plotting.py`                             | matplotlib figures → data URL |
| `src/drafter/history/utils.py` `image_to_bytes`/`repr_pil_image` | value previews (`safe_repr`)  |
| `src/drafter/history/serialization.py` `image_to_bytes`          | state dehydrate (dormant)     |
| `src/drafter/router/parameters/conversion.py`                    | upload → PIL conversion       |

**Conditional-Pillow plumbing to remove:** `components/utilities/image_support.py`
(`HAS_PILLOW`, `PILImage` stub, `refresh_pillow_support()`), plus every
"read as module attribute so the late micropip flip is observed" call site
(`images.py`, `files.py`, `conversion.py`, `history/*`, `launch.py`,
`site/site.py`, `client_server`).

**Two separate binary intake paths:**

1. Real uploads: bridge builds `{"filename", "content": bytes, "type",
   "size", "__file_upload__": True}` Python-side
   (`bridge/runtime.py handle_file_upload`); `convert_file_upload`
   (priority 10) dispatches on the annotation: `bytes` / `str` / `dict` /
   `DrafterBinaryFile` / `DrafterTextFile` / PIL `Image` subclass.
2. Component JSON payloads: Camera (and geolocation/microphone/map/audio)
   write `JSON.stringify({...})` into a hidden input with
   `data-transform="json-decode"`; Camera's dict carries `data_url`
   (PNG data URL from `canvas.toDataURL`). Converted to `Photo` by the
   predicate converter in `components/camera.py`.

**Two separate preview pipelines:**

- Structured describer for the State panel:
  `data/details/recursive_type_describer.py` emits `{kind: "pillow_image",
  value: <filename>}` — **bug:** the JS renderer
  (`js/src/debug/panels/state.tsx` case `"pillow_image"`) does
  `<img src={rep.value}>` and its test feeds a data URL, so Python's
  filename value renders broken images. `bytes`/`bytearray`/`BytesIO`/
  `DrafterBinaryFile` fall to `_visit_unknown` (bare `repr`).
- HTML-string `safe_repr` (`history/utils.py`) for route-parameter
  conversion records and test diffs: PIL with `.filename` becomes
  `<img src='{filename}'>` (broken for uploads — the filename is not a
  URL); otherwise base64 data URL. `history/formatting.py`
  `CustomPrettyPrinter` wraps the same for test output.

**State:** `SiteState` deep-copies state (PIL images deepcopy fine).
`history/serialization.py` `dehydrate_json`/`rehydrate_json` support PIL
(as latin1-encoded PNG strings) but **raise on raw `bytes`** — and are
exported yet currently called by nothing.

**Testing:** `assert_equal` delegates to bakery's `==`. Two PIL images are
never `==` even with identical pixels, so images in state or page content
make tests fragile. Failure *display* is PIL-aware (via
`CustomPrettyPrinter`), the pass/fail decision is not.

**Naming hazard (student-facing):** `from drafter import *` followed by
`from PIL import Image` silently shadows Drafter's `Image` component.
Any design that keeps students importing PIL directly keeps this trap.

---

## 2. Design goals

1. One image value type students can receive, store in state, manipulate,
   and hand back to components — without importing PIL themselves.
2. All four external forms convert cheaply in both directions:
   raw bytes, data URLs, files-with-metadata (filename/MIME), and URLs.
3. Debug panels render real thumbnails for images wherever values are
   shown (state panel, conversion records, test diffs).
4. `Image` component, `FileUpload`, `Camera`, and `Download` all speak the
   same type; annotations decide what a route receives.
5. Value semantics: `==` compares pixels, `repr` is short, deepcopy works,
   so `assert_equal` and state history behave.
6. Zero `HAS_PILLOW` conditionals anywhere.

---

## 3. The core type: `Picture`

### 3.1 Naming

Recommendation: **repurpose `Picture`** (today a bare alias of the `Image`
component) as the image *value* type, keeping `Image` as the *component*.
"`Image` shows a `Picture`" is a clean sentence for students, and the alias
has near-zero documented usage. Because `Picture`'s constructor accepts a
path/URL string (see below) and a `Picture` placed in page content
auto-wraps in an `Image` component (§6.1), old code that used
`Picture("dog.png")` as a component keeps working in the common case.

Alternatives considered:

- `ImageFile` — consistent with `DrafterBinaryFile`, but wrong connotation
  (the type is more than a file) and collides with `PIL.ImageFile`.
- `DrafterImage` — unambiguous but clunky for a name students type in
  every route annotation.
- Making the `Image` component itself the value type — rejected: mixes
  rendering concerns (width/height attrs, url handling) with data
  concerns, and the component's existing `open()`/`new()` instance
  methods show how awkward that hybrid already is.

### 3.2 Sketch

New module `src/drafter/data/images.py` — a *data-layer leaf* (like
`data/files.py` and `data/converter.py`) so the router, details, and
component layers can all import it without cycles.

```python
class Picture:
    """An image value: pixels plus optional file metadata."""

    # -- construction: one polymorphic constructor + explicit classmethods
    def __init__(self, source, filename=None, mime_type=None): ...
        # source: str (path, URL, or data URL — dispatched by sniffing),
        #         bytes/bytearray, PIL.Image.Image, Picture (copy),
        #         DrafterBinaryFile, Photo
    @classmethod
    def from_bytes(cls, data, filename=None, mime_type=None): ...
    @classmethod
    def from_data_url(cls, url): ...
    @classmethod
    def from_url(cls, url): ...        # lazy; see §3.3
    @classmethod
    def from_file(cls, path): ...      # via Drafter's environment-aware open
    @classmethod
    def from_pil(cls, image, filename=None): ...
    @classmethod
    def new(cls, width, height, color="white"): ...   # replaces Image.new

    # -- the four external forms, back out
    def to_bytes(self, format=None) -> bytes: ...     # encoded file bytes
    def to_data_url(self, format=None) -> str: ...
    def to_pil(self) -> PIL.Image.Image: ...
    def save(self, path, format=None) -> None: ...

    # -- metadata
    filename: str | None       # original upload/file name, if any
    mime_type: str             # sniffed or provided; default image/png
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...

    # -- curated manipulation (each returns a new Picture, PIL-style)
    def resize(self, width, height) -> "Picture": ...
    def scale(self, factor) -> "Picture": ...
    def rotate(self, degrees) -> "Picture": ...
    def crop(self, left, top, right, bottom) -> "Picture": ...
    def flip_horizontal(self) / flip_vertical(self) -> "Picture": ...
    def grayscale(self) -> "Picture": ...

    # -- pixel access (media-computation style)
    def get_pixel(self, x, y) -> tuple[int, int, int]: ...
    def set_pixel(self, x, y, color) -> None: ...     # mutates, documented

    # -- value semantics
    def __eq__(self, other): ...   # mode + size + tobytes comparison
    def __repr__(self): ...        # Picture('dog.png', 640x480, PNG) — never huge
    def __deepcopy__(self, memo): ...

    # -- escape hatch
    def __getattr__(self, name): ...
        # delegate unknown attrs to the underlying PIL image; wrap callables
        # so PIL.Image returns are re-wrapped as Picture
```

Notes:

- **Curated methods + delegation fallback.** The explicit methods give
  students autocomplete, docstrings, and friendly error messages
  (`resize` takes width/height, not a tuple). `__getattr__` keeps the
  full PIL surface available to advanced users without re-documenting it;
  re-wrapping returned `PIL.Image.Image` values means `pic.filter(...)`
  still yields a `Picture`. If the re-wrap magic feels too clever, ship
  the curated set first and add delegation later — it's additive.
- **Format policy:** remember the source format/MIME when known (upload
  `content_type`, data-URL prefix, file extension, PIL `format`);
  synthesized/manipulated images default to PNG (matches
  `canvas.toDataURL` and current behavior). `to_bytes(format="JPEG")`
  re-encodes on demand.
- **`__eq__` by pixels** makes `assert_equal` work on states and pages
  containing images. Define `__hash__ = None` explicitly (mutable via
  `set_pixel`).
- **Internal storage:** hold the decoded PIL image plus (when available)
  the original encoded bytes, so `to_bytes()` round-trips uploads
  byte-identically instead of re-encoding, and repeated `to_data_url()`
  calls don't re-encode.

### 3.3 Laziness for URL-backed pictures

`Picture("https://example.com/dog.png")` must not fetch at construction:
the dominant use is handing it to `Image`, which just needs the URL in
`src` (fetching would add CORS failures and latency where none exist
today). So a Picture holds a *source descriptor*; URL sources stay
unloaded until pixels/bytes are first requested, then load through
Drafter's environment-aware `open` (`files/opening.py`), which already
fetches over HTTP in Pyodide and downloads on desktop. A blocked fetch
(CORS, 404) raises a student-facing error naming the URL at the point of
pixel access. Local paths and everything else decode eagerly, so mistakes
surface at the line that made them.

---

## 4. Shared encoding helpers (consolidation)

Also in `data/images.py`, replacing the six copies:

- `pil_to_data_url(image, format="PNG") -> str`
- `encode_image(image, format) -> bytes`
- `decode_data_url(url) -> tuple[bytes, str]` (bytes, mime)
- `sniff_image_mime(data: bytes) -> str | None` (magic numbers; used by
  upload conversion and the bytes debug preview)
- `thumbnail_data_url(picture_or_pil, max_edge=128) -> str` (for debug
  telemetry — see §7)

`components/images.py`, `components/files.py`, `components/plotting.py`,
`history/utils.py`, `history/serialization.py`, and
`router/parameters/conversion.py` all switch to these.

---

## 5. Parameter conversion (router + components)

### 5.1 `Picture` converter (new, in `router/parameters/conversion.py`)

Registered for target `Picture`, accepting any of:

- `__file_upload__` dict → `Picture.from_bytes(content, filename=...,
  mime_type=type)`; friendly failure if the bytes don't decode as an
  image ("Perhaps the file is not an image…", mirroring the PIL branch).
- data URL string → `from_data_url`.
- camera-style JSON dict (has a `data_url` key) → `from_data_url`,
  so `Camera("pic")` + `def snap(state, pic: Picture)` works directly.
- plain URL/path string → lazy URL Picture.
- existing `Picture` / PIL image → pass through / wrap.

Keep the existing PIL-annotation branch of `convert_file_upload` working
(back-compat), but docs stop teaching it.

### 5.2 `bytes` from Camera

Extend the `bytes` path so a camera JSON dict (`data_url` present)
converts to decoded PNG bytes. Uploads already convert to `bytes`. Result:
"annotate `bytes`, get bits" holds for both FileUpload and Camera.

### 5.3 `Photo` refactor (camera.py)

`Photo` keeps its status-envelope role (permission workflow states must
remain inspectable without try/except) but gains the image:

- `Photo.picture: Picture | None` — property, lazily built from
  `data_url`. (Keep `data_url`/`width`/`height` fields for back-compat.)

Annotation decides what a route gets: `Photo` for the full envelope,
`Picture`/`bytes` for just the image (status failures convert to a
conversion failure with the status message, or `None` when annotated
Optional — see Open Questions).

### 5.4 Empty uploads

Today an empty upload with a PIL annotation silently yields `None` even
for non-Optional parameters. Proposed: `Picture | None` annotation →
`None`; bare `Picture` annotation → friendly conversion failure ("No file
was chosen. Did you mean to make the parameter optional?").

---

## 6. Components

### 6.1 `Image` component (`components/images.py`)

- Accepts `Picture`, PIL image, data URL, path/URL string — and now
  `bytes` (sniff MIME → data URL). All non-string forms go through
  `Picture` internally; the rendering branch becomes: data URL → as-is;
  unloaded URL Picture / string → URL handling; anything else →
  `picture.to_data_url()`.
- Default `alt` from `picture.filename` when no alt given (accessibility
  win for free).
- Deprecate the instance methods `Image.open()` / `Image.new()`
  (replaced by `Picture(...)` / `Picture.new(...)`).
- Delete the `HAS_PILLOW` guards.

**Auto-wrap in page content:** a `Picture` appearing directly in
`Page(state, [...])` content wraps in an `Image` component (same place
strings become `Text`). This is what lets `Picture` keep working for old
`Picture("dog.png")` component-style code, and it reads well for
students. Implemented in the page-content normalization path.

### 6.2 `Download` component and `Download` payload

Accept `Picture`/PIL: `href`/`content` from `to_bytes()`, MIME from the
picture, default `filename` from `picture.filename`. Both
`components/files.py` and `payloads/kinds/download.py`.

### 6.3 `FileUpload` / `Camera`

No component-side changes needed (the work is all in converters), but
docs/docstrings change to lead with `Picture`. Optional nice-to-have,
separate ticket: client-side thumbnail preview under a `FileUpload` that
accepted an image.

---

## 7. Debug panel & previews

### 7.1 Structured describer (`data/details/recursive_type_describer.py`)

- Replace the `pillow_image` visit with an `image` kind covering both
  `Picture` and raw PIL:
  `{kind: "image", value: <thumbnail data URL>, filename, width, height,
  mime, complexity}` — thumbnail via `thumbnail_data_url` (cap ~128px)
  so a 12-megapixel photo doesn't ship megabytes of telemetry on every
  state snapshot. This also fixes the existing bug where Python sends a
  filename and `state.tsx` expects a data URL.
- Add a `bytes` kind for `bytes`/`bytearray`: length + short hex preview;
  if `sniff_image_mime` recognizes it, include a thumbnail too (uploaded
  image kept as bits still previews).
- `DrafterBinaryFile`: describe as a small struct (filename, size, MIME),
  with thumbnail when the MIME/magic is an image.

### 7.2 JS (`js/src/debug/telemetry/state.ts`, `js/src/debug/panels/state.tsx`)

- Rename/extend `PillowImageRepresentation` → `ImageRepresentation`
  (kind `"image"`, plus filename/dimensions/mime fields); render
  thumbnail `<img>` with a caption line (`dog.png — 640×480 PNG`).
  Update the `pillow_image` tests. Add `BytesRepresentation` rendering.
- Keep CSS class names or rename `drafter-debug-rep-pillow-image` →
  `-image` across default + 98/XP/7 themes (theme parity checklist from
  the camera work applies).

### 7.3 String pipeline (`history/utils.py`, `history/formatting.py`)

- `safe_repr`: `Picture` → thumbnail `<img>` tag with title/alt from
  filename. Fix `repr_pil_image`'s filename branch — always use a data
  URL thumbnail (the filename is usually not a resolvable URL).
- `CustomPrettyPrinter`: route `Picture` through the same helper, so test
  diffs show thumbnails; `repr` fallback is the short `Picture(...)`
  form, never base64 dumps.

---

## 8. State, history, and serialization

- `SiteState` deepcopy: works via `Picture.__deepcopy__`. Note the memory
  cost of image-heavy state histories; the thumbnailing in §7 keeps
  *telemetry* small, but the Python-side history still holds full images.
  Acceptable for now; if it bites, add a history cap for large values
  (separate ticket).
- `history/serialization.py` (dormant): while touching it, (a) replace
  latin1-PNG hack with base64 via the shared helpers, (b) add
  `Picture` (`{__picture__: {data: <b64>, filename, mime}}`) and raw
  `bytes` (`{__bytes__: <b64>}`) support so the documented "state must be
  serializable" story includes images. If instead we decide dead code
  should die, delete the module and its exports — decide before Phase 4
  (see Open Questions).

---

## 9. Testing story

- `Picture.__eq__` (pixels + metadata-insensitive) makes
  `assert_equal(page_or_state_with_images, ...)` deterministic. Metadata
  (filename) intentionally does NOT affect equality — two identical
  screenshots from different files should be equal for students.
- Unit tests: round-trips (bytes ↔ data URL ↔ PIL ↔ Picture, upload dict
  → Picture, camera dict → Picture/bytes), lazy-URL behavior, empty
  upload, equality/repr/deepcopy, converter failure messages.
- JS tests: new `image`/`bytes` representation rendering (update
  `debug-panel.test.tsx`), no camera changes expected.
- Snippet/contract tests: `tests/components/test_components.py` entries
  unaffected except Image docstrings.

---

## 10. Pillow-as-hard-dependency cleanup

- Delete `components/utilities/image_support.py`; `from PIL import Image
  as PILImage` directly at each remaining use (mostly just
  `data/images.py` after consolidation).
- Remove `refresh_pillow_support()` calls (`launch.py`, `site/site.py`,
  `client_server`) and the module-attribute-read convention.
- Pyodide: Pillow is already in the system-package preload
  (`js/src/pyodide.index.tsx`); verify it loads *before* first
  `import drafter` in all entry paths (index, docs demos, tests) since
  the lazy re-import escape hatch goes away. Check the pyodide-wheel
  prefetch list used by jest e2e.
- Desktop: already a hard dependency in `pyproject.toml`.

---

## 11. Phasing

1. **Core type.** `data/images.py`: `Picture`, encoding helpers, tests.
   No behavior changes elsewhere.
2. **Hard-dependency cleanup.** Delete `image_support`, drop all
   `HAS_PILLOW` branches, verify Pyodide load order. (Do this second so
   phase 1 code never writes new conditionals.)
3. **Converters.** `Picture` converter, camera-`bytes`, `Photo.picture`,
   empty-upload policy. Router tests.
4. **Components.** `Image` accepts everything + auto-wrap in page
   content; `Download` component/payload; deprecations. Serialization
   decision (extend or delete) lands here.
5. **Debug & previews.** Describer `image`/`bytes` kinds (bug fix),
   JS telemetry/panels/tests/CSS themes, `safe_repr`/pretty-printer.
6. **Docs & examples.** Student-facing images guide (upload → manipulate
   → display → download; camera → Picture), reference updates, example
   programs; deprecate PIL-annotation docs.

Phases 1–2 are pure groundwork; 3–5 each ship independently useful
behavior; 6 closes it out.

---

## 12. Open questions

1. **Naming:** confirm repurposing `Picture` vs a fresh name
   (`ImageFile`, `DrafterImage`). Everything else in the plan is
   name-agnostic.
    Answer: Confirmed, `Picture` is the name choice.
2. **`__getattr__` PIL delegation:** ship in phase 1, or curated methods
   only until a need appears?
    Answer: Let's skip doing this for now. Too likely to cause confusion. We can add it later. For now, expect students to use the curated methods, and if they need more advanced functionality, they can convert to a PIL image using `to_pil()` and use the full PIL API.
3. **Empty-upload policy** (§5.4): friendly failure vs `None`
   pass-through for non-Optional `Picture`.
     Answer: Let's go with friendly failure for non-Optional `Picture` parameters. This will help students understand that they need to provide a file and will guide them towards making the parameter Optional (using the `| None` syntax) if they want to allow for no file being chosen.
4. **`history/serialization.py`:** extend for Picture/bytes, or delete as
   dead code?
     Answer: I have deleted that file now.
5. **Camera → `Picture` when status is denied/error:** conversion failure
   (blocks the route with a friendly message) vs `None` (requires
   Optional annotation)? Leaning: mirror the empty-upload policy.
     Answer: Same as above, friendly failure for non-Optional `Picture` parameters. Users should be encouraged to use Photo or Optional[Picture] if they want to handle cases where the camera is denied or there is an error.
6. **`plotting.py`:** should chart components expose their rendered
   output as `Picture` too (e.g. for download)? Cheap once helpers are
   shared; decide in phase 4.
     Answer: There should be a way to get the rendered output as a Picture, but that shouldn't be the default behavior.
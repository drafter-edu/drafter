1. **Google sections**: `Args:` / `Returns:` / `Raises:` / `Yields:` / `Attributes:` /
   `Note:` / `Example:`. Blank line between sections.
2. **No types in Args parentheses.** The codebase is type-annotated; mkdocstrings pulls
   types from annotations. This retires the recurring `**kwargs (dict):` and
   `context (dict):` errors — write `**kwargs: Additional HTML attributes.`.
3. **Class attributes**: document dataclass fields and public instance attributes in the
   class docstring `Attributes:` section, in **field-declaration order** (order mismatch
   is how drift hides). `#:` or post-assignment string docstrings acceptable for
   `converter.py`-style registries.
4. **Top-level constants**: PEP 224-style string literal immediately after the
   assignment (griffe/mkdocstrings parses these). One line for self-evident constants.
5. **No TODOs inside docstrings.** Move to `#` comments or issues. A docstring describes
   what the code does today.
6. **No Sphinx roles** (`:class:`, `:data:`). Use plain backticks, or mkdocstrings
   cross-references (`[Page][drafter.payloads.kinds.page.Page]`) where a link matters.
7. **Base classes document the base contract**, not a subclass's behavior
   (`RuntimeAdapter.promise_data`, `Fragment.verify` violations).
8. **Student-facing API gets examples.** Components, styling functions, testing
   assertions, `Page`/`Fragment`/`Download`/`Redirect` should carry a short
   `Example:` block — these render into the mkdocs site students read.
9. **`Raises:` is mandatory** when the function raises deliberately.
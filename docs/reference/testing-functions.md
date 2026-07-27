---
page_type: reference
title: Testing functions
level: L2
audience: S
priority: P1
prereqs: []
symbols:
  - assert_equal
  - assert_page
  - assert_state
  - assert_content
  - assert_has
  - assert_in
  - assert_not_has
  - assert_not_in
  - assert_has_regex
  - assert_in_regex
  - assert_attribute
  - assert_style
  - assert_children
  - assert_text
  - set_assertion_defaults
outcome: Look up every assertion.
---

# Testing functions

Every assertion Drafter ships. They all behave the same way: print
SUCCESS or FAILURE (with every difference found), return `True` or
`False`, and never crash your program. They run where they are
written, before `start_server(...)`, and report into the debug
panel's Tests tab. The how-to is
[Test a feature](../add/test-a-feature.md).

## Shared flags

Every assertion accepts these keyword flags:

| Flag | Default | Meaning |
| ---- | ------- | ------- |
| `precision` | `None` | Decimal places for float comparisons. |
| `exact_strings` | loose | Make text matching exact (case and whitespace count). |
| `strict_styles` | off | Make style differences count as failures. |
| `quiet` | `False` | Suppress the SUCCESS line on passing tests. |

By default, matching is forgiving on purpose: case-insensitive
text, styles ignored. Change the defaults for a whole file with
`set_assertion_defaults`, below.

## Comparing whole things

### assert_equal

```python
assert_equal(save_task(State([]), "nap"), Page(State(["nap"]), [...]))
```

The general-purpose comparison: any two values, numbers, strings,
lists, dataclasses, components, or whole pages, with every
difference reported. This is what
[frozen page tests](../add/freeze-pages.md) use.

### assert_page

```python
assert_page(index(State(3)), Page(State(3), ["Score: 3\n", Button("Play", "play")]))
```

Like `assert_equal`, but says what you mean when both sides are
pages: state and content both compared.

### assert_state

```python
assert_state(feed(State(5)), State(4))
```

Compares only the state. Either side can be a page (its state is
extracted) or a bare state value. The workhorse for testing rules.

### assert_content

```python
assert_content(index(State(3)), ["Score: 3\n", Button("Play", "play")])
```

Compares only the content, ignoring state. Either side can be a
page, a content list, or a single component or string.

## Searching within a page

### assert_has and assert_in

```python
assert_has(index(state), Button("Play", "play"))
assert_in("Score:", index(state))
```

Check that content appears *somewhere* in the page. The needle can
be a string (matched against page text, partial matches included)
or a component (matched structurally, position ignored). `assert_in`
is the same check with the arguments in `needle in page` order.
Text needles do not reach inside `Table` rows; use a component
needle (`assert_has(page, Table([...]))`) for tables.

### assert_not_has and assert_not_in

```python
assert_not_has(index(logged_out), Button("Log out", "do_logout"))
```

The same searches, passing when the needle is absent.

### assert_has_regex and assert_in_regex

```python
assert_has_regex(results(state), r"scored \d+ out of \d+")
```

Match page text against a regular expression, for when the wording
varies but the shape should not.

## Inspecting one component

### assert_attribute

```python
assert_attribute(Button("Play", "play"), "url", "play")
```

Check one field or setting of a component, like a button's `text`
or `url`.

### assert_style

```python
assert_style(bold("Hi"), "font_weight", "bold")
```

Check one CSS style set directly on a component via helpers,
`style_*` keywords, or `update_style`. The other assertions ignore
styles by default; this one exists to test them.

### assert_children

```python
assert_children(BulletedList(["a", "b"]), ["a", "b"])
```

Check what is nested inside a component: list items, a Div's
contents.

### assert_text

```python
assert_text(index(state), "The Pet Quiz\nThree questions. No pressure.")
```

Collect all visible text of a page or component, joined with
newlines, and compare it, ignoring structure and styling entirely.

## Changing the defaults

### set_assertion_defaults

```python
set_assertion_defaults(strict_styles=True)
```

Change the default flags for every assertion after this call: any
of `precision`, `exact_strings`, `strict_styles`, and
`report_success`. Only the flags you pass change. The flags are
keyword arguments, so spell them out (`strict_styles=True`).

## Notes

- Assertions return booleans and print failures rather than raising,
  so one failing test never hides the ones after it.
- Failing tests do not stop the site from starting; they report in
  the terminal and the debug panel. Read the Tests tab.
- Routes are host-callable functions: build a state, call the route,
  assert on the result. No clicking is ever required to test logic.
- A `Page` is a dataclass with `state` and `content` fields, so when
  no assertion fits, inspect the pieces yourself:
  `assert_equal(index(State(5)).state.score, 5)`.

## Related

- [Test a feature](../add/test-a-feature.md): choosing the right
  assertion, with worked examples.
- [Freeze finished pages](../add/freeze-pages.md): regression tests
  from the debug panel.

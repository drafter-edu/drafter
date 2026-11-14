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

This page lists every assertion Drafter ships. They all behave the
same way: each prints SUCCESS or FAILURE (with the differences it
found), returns `True` or `False`, and never crashes your program.
Assertions run where they are written, before `start_server(...)`,
and report into the debug panel's Tests tab. The how-to is
[Test a feature](../add/test-a-feature.md).

## Shared flags

Most assertions accept the same four keyword flags.

| Flag | Default | Meaning |
| ---- | ------- | ------- |
| `precision` | 4 decimal places | How many decimal places are compared when two floats are compared. With the default, `1.00001` and `1.00002` count as equal. |
| `exact_strings` | `False` | When `True`, text must match exactly, including capital letters and spaces at either end. |
| `strict_styles` | `False` | When `True`, a difference in styling counts as a failure. |
| `quiet` | `False` | When `True`, this one call does not print its SUCCESS line. A FAILURE is always printed. |

Four assertions accept only `exact_strings` and `quiet`. They are
`assert_has_regex`, `assert_in_regex`, `assert_style`, and
`assert_text`. Passing `precision` or `strict_styles` to one of them
raises a `TypeError`.

With the default flags, matching is forgiving. Text comparisons ignore
capital letters and spaces at either end, and styles are left out of
comparisons entirely. Change the defaults for a whole file with
`set_assertion_defaults`, described below.

## Comparing whole things

### assert_equal

```python
assert_equal(save_task(State([]), "nap"), Page(State(["nap"]), [...]))
```

The general-purpose comparison. It accepts any two values (numbers,
strings, lists, dataclasses, components, or whole pages) and reports
every difference it finds. This is what
[frozen page tests](../add/freeze-pages.md) use.

### assert_page

```python
assert_page(index(State(3)), Page(State(3), ["Score: 3\n", Button("Play", "play")]))
```

Like `assert_equal`, but written for the case where both sides are
pages: the state and the content are both compared.

### assert_state

```python
assert_state(feed(State(5)), State(4))
```

Compares only the state. Either side can be a page (its state is
extracted) or a bare state value. This is the assertion you will use
most often for testing your app's rules.

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
Text needles do not match text inside `Table` rows; use a component
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

Match page text against a regular expression. This is useful when
the exact wording varies but the overall pattern should not.

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
assert_children(Div("a", "b"), ["a", "b"])
```

Check what is nested inside a component, such as the contents of a
`Div` or a `Span`. For the items of a `BulletedList`, check the
`items` attribute:
`assert_attribute(BulletedList(["a", "b"]), "items", ["a", "b"])`.

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
`report_success`. Only the flags you pass change. Pass each flag by
name, as in `strict_styles=True`.

`report_success` is the whole-file form of `quiet`.
`set_assertion_defaults(report_success=False)` stops every passing
assertion from printing its SUCCESS line, and `quiet=True` does the
same for one call. A SUCCESS line is printed only when `quiet` is
`False` and `report_success` is `True`. Neither setting hides a
FAILURE.

## Notes

- Assertions return booleans and print failures rather than raising,
  so one failing test never hides the ones after it.
- A failing test does not stop the site from starting. The failure
  is reported in the terminal and in the debug panel's Tests tab, and
  the site runs as usual. Python's own `assert` statement behaves
  differently: when it fails, it raises `AssertionError`, and the
  program stops before it reaches `start_server`.
- Routes are ordinary functions you can call directly: build a
  state, call the route, and assert on the result. You never need to
  click through the app to test its logic.
- A `Page` is a dataclass with `state` and `content` fields, so when
  no assertion fits, inspect the pieces yourself:
  `assert_equal(index(State(5)).state.score, 5)`.

## Related

- [Test a feature](../add/test-a-feature.md): choosing the right
  assertion, with worked examples.
- [Freeze finished pages](../add/freeze-pages.md): regression tests
  from the debug panel.

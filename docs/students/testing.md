# Testing Drafter Applications

A powerful feature of Drafter is the ability to test your website, just like
you test any other code. Every route in Drafter is a simple function: it takes
in a `State` and returns a `Page`. That means you can call a route yourself,
look at the `Page` it returns, and check that it is what you expected.

Drafter comes with a whole family of `assert_` functions to make those checks
easy to write and easy to read. You do not need to install anything extra —
they are all part of Drafter:

```python
from drafter import *

@dataclass
class State:
    name: str

@route
def index(state: State) -> Page:
    return Page(state, [
        f"Hello, {state.name}!"
    ])

assert_page(index(State("World")),
            Page(State("World"), ["Hello, World!"]))

start_server(State("World"))
```

When a test passes, you will see a message like this in the console:

```
SUCCESS at line 14 (assert_page)
```

When a test fails, Drafter prints a friendly explanation of exactly *what* was
different and *where*:

```
FAILURE at line 14 (assert_page):
    The page was different from what the test expected:
      - In Page content index '0': Expected 'Goodbye, World!' but got 'Hello, World!'
```

Failed tests never crash your program — they print their message, and your
other tests keep running. Every test also shows up in the **Your Tests**
section of the Debug Information at the bottom of your website, with a
side-by-side comparison of what you expected and what you actually got.

## The Big Idea: Test What Matters

You *can* test that an entire page is exactly right, and sometimes that is
what you want. But often, you only care about one thing: "Did the score go
up?" or "Is there a Save button on this page?" Drafter has an assertion for
each of these situations, so your tests can focus on what actually matters:

| Function | What it checks |
|----------|----------------|
| `assert_page(page, expected_page)` | The whole page: state *and* content |
| `assert_state(page, expected_state)` | Just the page's state |
| `assert_content(page, expected_content)` | Just the page's content |
| `assert_has(page, needle)` | The page contains some text or component, *anywhere* |
| `assert_text(page, expected_text)` | The page's visible text, ignoring structure |

There are also tools for checking one specific component
(`assert_attribute`, `assert_style`, `assert_children`) and for advanced
text matching (`assert_has_regex`). We will look at each one below, using
this little game as our running example:

```python
from drafter import *

@dataclass
class State:
    score: int

@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Cookie Game"),
        f"Your score is {state.score}",
        Button("Click me!", add_point)
    ])

@route
def add_point(state: State) -> Page:
    state.score += 1
    return index(state)
```

## Testing the State: `assert_state`

Use `assert_state` when you care about the *data*, not the appearance. It
compares only the state of the page:

```python
assert_state(add_point(State(5)), State(6))
```

You can hand it the whole `Page` that your route returned — Drafter will pull
out the state for you. If the state is wrong, the message tells you which
field was wrong:

```
FAILURE at line 20 (assert_state):
    The page's state was different from what the test expected:
      - In State score: Expected 6 but got 5
```

## Testing the Content: `assert_content`

Use `assert_content` when you care about what is *shown*, and not about the
state. The expected content can be a list, a single component, or even just a
string:

```python
assert_content(index(State(5)), [
    Header("Cookie Game"),
    "Your score is 5",
    Button("Click me!", add_point)
])
```

## Checking That Something Is On the Page: `assert_has`

Often you do not want to describe the entire page — you just want to know
that *something* is there. `assert_has` searches the whole page for you,
no matter how deeply nested the content is:

```python
page = index(State(5))

# Is this text anywhere on the page?
assert_has(page, "your score is 5")

# Even just part of the text is enough:
assert_has(page, "score")

# Is there a button that says "Click me!" and goes to add_point?
assert_has(page, Button("Click me!", add_point))
```

If the search fails, Drafter shows you what text the page *did* have, so you
can spot typos quickly:

```
FAILURE at line 25 (assert_has):
    Could not find 'Your scor is 5' anywhere in the page:
      - The page's text was: 'Cookie Game', 'Your score is 5', 'Click me!'
```

If you prefer to write the needle first (like Python's `in` operator), use
`assert_in` instead — it is the same check with the arguments flipped:

```python
assert_in("score", page)
```

And to check that something is *not* on the page, use `assert_not_has` or
`assert_not_in`:

```python
assert_not_has(page, "Game Over")
```

## Testing Just the Words: `assert_text`

`assert_text` gathers up all the visible text of a page (or a single
component) and compares it as one big chunk. It completely ignores structure,
components, and styling — only the words matter:

```python
assert_text(index(State(5)), "Cookie Game your score is 5 click me!")
```

## Checking One Component's Details

Sometimes you want to zoom in on a single component and check something
specific about it. First grab the component (remember, `page.content` is just
a list!), then use one of these:

```python
page = index(State(5))
button = page.content[2]

# Check one attribute of the component:
assert_attribute(button, "text", "Click me!")
assert_attribute(button, "url", add_point)

# Check the component's nested content:
assert_children(page.content[0], "Cookie Game")
```

If you ask about an attribute that does not exist, Drafter lists the ones
that do:

```
FAILURE at line 31 (assert_attribute):
    The Button does not have an attribute named 'label':
      - The attributes available are: arguments, text, url
```

### Checking Styles: `assert_style`

Normally, Drafter's tests ignore styling completely (more on that below). But
if styling is the thing you *want* to test, use `assert_style`:

```python
fancy = Button("Click me!", add_point, style_color="red")
assert_style(fancy, "color", "red")
```

This works for styles set with `style_` keyword parameters, with helper
functions like `change_color`, or with a raw `style="..."` string. Note that
it can only see styles set directly on the component — styles that come from
CSS files or themes are invisible to it.

## Advanced Text Matching: `assert_has_regex`

If you know about [regular expressions](https://docs.python.org/3/howto/regex.html),
you can match patterns of text instead of exact text. For example, to check
that the page shows *some* score, without caring which number:

```python
assert_has_regex(index(State(5)), r"your score is \d+")
```

(`assert_in_regex` is the same thing with the pattern first.)
If you have never heard of regular expressions, feel free to skip this one —
`assert_has` covers most situations.

## Loose By Default, Strict When You Want

Drafter's assertions are deliberately forgiving, so your tests do not break
over things that usually do not matter:

* **Capitalization and extra spaces are ignored.** `"hello"` matches
  `"  Hello "`.
* **Styling is ignored.** A red button and a plain button count as the same
  button, so making your site prettier does not break your tests.
* **Decimals are rounded.** Floats only need to match to 4 decimal places, so
  `0.1 + 0.2` equals `0.3`.

Each assertion accepts flags to change this for a single test:

```python
# Now capitalization and spacing must match exactly:
assert_has(page, "Your score is 5", exact_strings=True)

# Now style differences count as failures:
assert_content(page, [plain_button], strict_styles=True)

# Now floats must match to 8 decimal places:
assert_state(result, State(0.333333333), precision=8)
```

You can also change the default for *all* of your tests at once with
`set_assertion_defaults`. For example, if an assignment is all about styling:

```python
set_assertion_defaults(strict_styles=True)
```

## Automatically Generated Tests

When you run your Drafter application, Drafter automatically creates tests
for you as you interact with the site.

The Debug Information at the bottom of the page includes a section titled
**Page Load History**. Clicking on the **Page Content** arrow will reveal the
generated Page content, which can be copy/pasted back into your code as an
`assert_equal` along with the appropriate **Call**.

You might think of this as "freezing" the expected state of the website, once
you are happy with the design. If a later change accidentally breaks an old
page, one of these tests will fail and tell you exactly what changed. Tests
that protect finished features like this are known as **regression tests**.

## Testing Pieces By Hand

Everything above is built on one simple fact: a `Page` is just a dataclass
with a `state` field and a `content` list. So if none of the assertions fit
what you want to check, you can always inspect the pieces yourself:

```python
result = index(State(5))
assert_equal(result.state.score, 5)
assert_equal(len(result.content), 3)
```

`assert_equal` compares any two values — numbers, strings, lists,
dataclasses, components, or whole pages — and reports every difference it
finds. (If you have used the `bakery` library in class before:
`from bakery import assert_equal` still works in Drafter, but the built-in
`assert_equal` gives you much more detailed messages for pages and
components.)

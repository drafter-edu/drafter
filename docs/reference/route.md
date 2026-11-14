---
page_type: reference
title: route
level: L1
audience: S
priority: P0
prereqs: []
symbols:
  - route
  - add_route
outcome: Know exact route decorator behavior.
---

# route

`@route` registers a function with Drafter so that buttons, links, and
addresses can reach it. A route is not a page; it is a function that
builds and returns a [Page](page.md) each time someone arrives.

## Syntax

```python
@route
def some_name(state: State) -> Page: ...

@route("other-address")
def some_name(state: State) -> Page: ...
```

| Form | Meaning |
| ---- | ------- |
| `@route` | Register under the function's own name. `def feed(...)` becomes the address `feed`. |
| `@route("url")` | Register under a custom address instead of the function name. |
| `add_route(url, function)` | Do the same thing without decorator syntax. Rarely needed. |

## The name becomes the address

The route registered from `def feed(...)` is what
`Button("Feed", "feed")` points at, and what the browser shows as the
page's address. The route named `index` is special: it builds the
front page shown when your app starts, and every app must have one.

```python drafter height=220
from drafter import *


@route
def index() -> Page:
    return Page([
        "The front page.\n",
        Button("Visit the other page", "second")
    ])


@route
def second() -> Page:
    return Page([
        "The route named second built this page.\n",
        Button("Home", "index")
    ])


start_server()
```

## How parameters are filled

When a route runs, Drafter fills its parameters in a fixed order:

1. **State comes first.** If the first parameter is named `state`, it
   receives the current state. (Drafter can usually still identify the
   state parameter if you name it something else, but `state` is the
   convention and the docs use it everywhere.)
2. **Form values bind by name.** Each input component's `name` must
   match a parameter: `TextBox("guess")` fills a parameter called
   `guess`. The parameter's type annotation controls conversion, so
   `guess: int` receives a number. See
   [Forms and input](../concepts/forms-and-input.md).
3. **Button arguments bind by name too.** `Argument("prize", "gold")`
   attached to a button fills a parameter called `prize`.

A required parameter that nothing fills stops the request with a
[missing parameter](../help/errors/missing-parameter.md) error. A value
that cannot be converted to the annotated type stops it with a
[conversion error](../help/errors/type-conversion-int.md). The table
under [Parameter conversion](#parameter-conversion) lists every
annotation that Drafter converts.

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    record: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Last entry: " + state.record + "\n",
        "Pet name:",
        TextBox("pet_name"),
        "\nAge:",
        TextBox("pet_age"),
        "\n",
        Button("Save", "save")
    ])


@route
def save(state: State, pet_name: str, pet_age: int) -> Page:
    state.record = pet_name + " (" + str(pet_age) + " years old)"
    return index(state)


start_server(State("none yet"))
```

## Parameter conversion

Values from the browser arrive as text. The type annotation on a
parameter tells Drafter what to turn that text into before the route
runs. When a value cannot be converted, the request stops with an
error page titled `Problem With the Route's Arguments`, and the
message names the parameter and the value that was sent.

| Annotation | The route receives | Details |
| ---------- | ------------------ | ------- |
| none | The value as it was sent. | Nothing is converted. A text input sends a `str`. |
| `str` | The text exactly as typed. | Spaces at either end are kept. An empty box gives `""`. |
| `int` | A whole number. | Spaces around the number are ignored, and `5.0` is accepted as `5`. Text such as `2.5`, `twenty`, or `1,000` is an error, and so is an empty box. |
| `float` | A decimal number. | `3` becomes `3.0`. Text that is not a number is an error, and so is an empty box. |
| `bool` | `True` or `False`. | `true`, `on`, `1`, `yes`, and `checked` give `True`. `false`, `off`, `0`, `no`, and empty text give `False`. Capital letters make no difference. A `CheckBox` gives `True` when it is checked and `False` when it is not. Any other text is an error. |
| `list`, `list[str]`, `list[int]` | A list. | Each item is converted to the type in the brackets. One value alone becomes a one-item list. A `SelectBox` with `multiple=True` sends one item for each selected option. |
| `tuple[int, int]`, `tuple[int, ...]`, `set[str]` | A tuple or a set. | The items are converted as they are for a list. A tuple that names a type for each position must receive exactly that many values. |
| `Literal["red", "blue"]` | The value, when it is one of the listed choices. | `Literal[1, 2, 3]` turns the text `2` into the number `2`. Any other value is an error that lists the choices. |
| `int | float` and other unions | The result from the first type that accepts the value. | The types are tried from left to right. With `int | float`, the text `2` gives `2` and the text `2.5` gives `2.5`. When `str` is one of the types, text is passed through unchanged. |
| `int | None`, `Optional[int]` | The same result as `int`. | Adding `None` does not make the parameter optional, and an empty box is still an error. The one exception is listed with `Picture` below. |
| a default, as in `times: int = 1` | The default, when no value with that name was sent. | A value that was sent is still converted by the annotation. |
| `**kwargs` | A dictionary of every value that matched no named parameter. | These values are not converted. |
| `date`, `time`, `datetime` | A value from Python's `datetime` module. | The text must be in ISO form, such as `2026-11-14`, `13:30`, or `2026-11-14T13:30`, which is the form that date and time inputs send. Empty text gives the current date or time. Other forms, such as `11/14/2026`, are an error. |
| a dataclass | An instance of the dataclass. | The value must be a dictionary, or JSON text, with a key for each field. Each field is converted by its own annotation, and fields that have defaults may be left out. |
| `dict` | The dictionary that was sent. | JSON text is not turned into a dictionary. An uploaded file gives a dictionary with the keys `filename`, `content`, `type`, and `size`. |
| `Color` | A [Color](data-types/color.md). | The text can be a hex code such as `#ff8800` or a color name such as `red`. A `ColorPicker` sends a hex code. With `list[int]`, a hex code becomes `[255, 136, 0]`. |
| `Picture` | A [Picture](data-types/picture.md) made from an uploaded image. | A file that is not an image is an error. With `Picture | None`, the route receives `None` when no file was chosen. |
| `str`, `bytes`, `DrafterTextFile`, `DrafterBinaryFile` on a `FileUpload` | The file's text, its raw bytes, or its contents together with the filename. | [File types](data-types/file-types.md) describes each one. For `str`, a file that is not UTF-8 text is an error. |
| `Photo`, `Location`, `Recording`, `AudioLevel` | A value built from the data that a camera, location, or sound component sends. | [Data types](data-types/index.md) describes each one. |

Two rules explain most surprises:

- **An empty text box still sends a value.** The value is empty text,
  so the parameter is not missing, and its default is not used. For a
  number field that may be left empty, annotate the parameter as `str`
  and convert the text yourself after checking for `""`.
- **A value that matches no parameter is not an error.** The route
  still runs, and the debug panel shows a warning that names the unused
  value. A route with `**kwargs` receives those values without a
  warning.

## Built-in routes

Drafter adds a few routes of its own to every app. Their names start
with `--`, so they are separate from your routes, and you can still
name your own routes `about` or `reset`. A `Button` or `Link` can
target a built-in route by its name.

| Route | What it does |
| ----- | ------------ |
| `--about` | Shows the About page, which lists the site title and the details given to [`set_site_information`](site-config.md#set_site_information). When no details were given, the page says so. |
| `--reset` | Puts the state back to the value that was passed to `start_server`, and then shows the `index` page. |
| `--bug-report` | Shows a page that explains when to report a problem with Drafter and offers a **Download Bug Report** button. |
| `--stop-server` | Shows a page that asks for confirmation. Its button ends the program that is running on your computer, the same as pressing Ctrl+C in the terminal. |

Two more names, `--error` and `--reload`, are used by Drafter's own
error pages. They are not meant to be targets for your buttons.

The most common use is a button that starts the app over:

```python
@route
def index(state: State) -> Page:
    return Page(state, [
        "Count: " + str(state.count) + "\n",
        Button("Add one", "add"),
        Button("Start over", "--reset")
    ])
```

Clicking **Start over** returns the state to its starting value and
shows the front page. The address bar then ends with `?route=--reset`.
The browser's Back button still returns to the page the visitor was on,
with the state that page had.

## Opening a site on a route

After each navigation, the address bar ends with `?route=` and the
name of the route that built the page, as in
`http://localhost:8000/?route=second`. Opening an address of that form
starts the site and runs that route in place of `index`.

Three limits apply to an address like this:

- **The state starts fresh.** The route receives the state that was
  passed to `start_server`, not the state from an earlier visit.
  Reloading the browser tab has the same effect, because the address
  still names the last route.
- **Only the route name is used.** Other values in the address are not
  passed to the route, so `?route=greet&who=Ada` runs `greet` without a
  value for `who`. An address like this is dependable only for a route
  that needs nothing but the state. A route with a required form
  parameter shows the `Problem With the Route's Arguments` error page.
- **The name must match a route.** Any other name shows the
  `Page Not Found` error page.

On the development server, a shorter form also works. The address
`http://localhost:8000/second` is redirected to
`http://localhost:8000/?route=second`.

A site built with `drafter --compile` includes a file named `404.html`
that performs the same redirect on GitHub Pages. With that file in
place, `https://your-username.github.io/your-repository/--about` opens
the About page of the deployed site. The redirect expects the usual
GitHub Pages project address, in which the site sits one folder below
the domain. The [`--create-404`](cli.md#building-for-deployment) flag
controls whether the file is written.

## Parameters that Drafter supplies

A parameter with one of three reserved names is filled by Drafter
itself, not by a form value.

| Parameter | What it receives |
| --------- | ---------------- |
| `_request` | The request being handled. `_request.url` is the name of the route that was asked for, and `_request.kwargs` is a dictionary of the values that were sent, before any conversion. |
| `_configuration` | The site's settings. For example, `_configuration.site_title` is the site title and `_configuration.theme` is the name of the theme. |
| `_server` | The object that runs the app. Drafter's own pages use it, and most apps never need it. |

```python
@route
def where(state: State, _request) -> Page:
    return Page(state, [
        "The route named " + _request.url + " built this page."
    ])
```

Avoid other parameter names that begin with an underscore. Drafter
treats every such name as one of its own, so it does not check that a
value was sent for the parameter. When nothing fills the parameter,
the route fails with Python's own `missing 1 required positional
argument` error in place of the usual missing parameter message.

## Notes

- **Route names must be unique.** If you define two functions with the
  same name, Python silently keeps only the second definition; this is
  Python's behavior, not Drafter's.
- **Routes are ordinary functions.** You can call one from another
  (`return index(state)`) and call them directly in tests
  (`assert_state(save(State("x"), "Ada", 4), State("Ada (4 years old)"))`).
- **Custom addresses** from `@route("...")` are normalized before
  matching: extra slashes are trimmed, and in the most heavily cleaned
  form, only letters, numbers, and underscores are kept. Buttons and
  links can target the custom address string.
- **Names that start with `--` belong to Drafter.** The
  [built-in routes](#built-in-routes) use that prefix, so you can name
  your own routes `about` or `reset` without replacing them.

## Related

- [Page](page.md): what a route returns.
- [Routes and pages](../concepts/routes-and-pages.md): the concept.
- [Add and connect pages](../add/pages.md): the how-to.
- [Link or button points to an unknown route](../help/errors/route-not-found.md):
  the most common routing mistake.

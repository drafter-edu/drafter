---
page_type: how-to
title: JavaScript interop
level: L4
audience: S
priority: P2
prereqs: [extend/pyodide]
symbols: []
outcome: Call JavaScript when Python is not enough.
---

# JavaScript interop

## Goal

Use the browser's own abilities from your Python code. A browser
can measure its window, change a page that is already showing,
copy text to the clipboard, and run JavaScript libraries. This page
shows how to reach each of those, for the rare feature that no
component covers.

## Before you start

You have read [Python in the browser](pyodide.md), which explains
that your routes run inside the visitor's browser. Everything on
this page depends on that fact. The techniques here work, but they
have more ways to go wrong than the rest of Drafter. Before you
use one, look through the
[component list](../reference/components/index.md), because most
features that seem to need JavaScript already have a component.

JavaScript is the programming language that browsers run directly.
You do not need to know any of it for the first half of this page.
The later recipes contain a few lines of JavaScript, and each line
is explained where it appears.

## The `js` module

Pyodide provides a module named `js` that presents the browser's
JavaScript objects as Python objects. `js.window` is the browser
window, `js.document` is the page inside it, and `js.navigator`
describes the browser itself. You read their values and call their
functions with ordinary Python syntax.

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    report: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Browser Inspector"),
        Button("Inspect my browser", "inspect"),
        "\n" + state.report
    ])


@route
def inspect(state: State) -> Page:
    import js
    state.report = ("Your window is "
                    + str(js.window.innerWidth) + " by "
                    + str(js.window.innerHeight)
                    + " pixels, and your browser calls itself: "
                    + str(js.navigator.userAgent)[:60] + "...")
    return index(state)


start_server(State(""))
```

A number or a piece of text that comes from JavaScript arrives as
an ordinary Python `int`, `float`, or `str`. Anything else, such as
an element of the page, arrives as a wrapper object that has
meaning only inside the browser.

### One file, two places

Every recipe on this page shares one constraint. The `js` module
exists only in the browser, and your file runs in two places.
It runs first on your own computer, where your tests execute, and
then again in the browser, as
[Python in the browser](pyodide.md) describes. Your computer has
no `js` module, so an import at the top of the file stops the
program there, before any site appears.

```python
import js
```

```text
ModuleNotFoundError: No module named 'js'
```

The demo above avoids the error by putting the import inside the
route. The `inspect` route runs only when a visitor clicks the
button, and visitors click in the browser. That fix has a limit,
because a test also calls a route, and tests run on your computer.
A test of the `inspect` route would stop with the same error.

The pattern that works in both places is to ask Python where it
is running, and to keep the code that needs the browser in one
small function.

```python drafter height=260
from drafter import *
from dataclasses import dataclass
import sys

IN_BROWSER = sys.platform == "emscripten"


@dataclass
class State:
    pass


def window_width() -> int:
    if not IN_BROWSER:
        return 1024
    import js
    return int(js.window.innerWidth)


def describe_width(width: int) -> str:
    if width < 600:
        return "a narrow window, probably on a phone"
    return "a wide window"


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Window Check"),
        "You are using " + describe_width(window_width()) + "."
    ])


assert_equal(describe_width(400), "a narrow window, probably on a phone")
assert_equal(describe_width(1280), "a wide window")
assert_has(index(State()), Header("Window Check"))

start_server(State())
```

`sys.platform` is `"emscripten"` inside the browser and something
else on your computer. `window_width` reaches for `js` only in the
browser and returns a stand-in value everywhere else.
`describe_width` makes the decision and never touches `js`, so the
first two tests check it with widths of their own choosing. The
third test calls the route itself. It passes in both places because
it checks only the header, which does not depend on the
measurement.

The recipes below keep the import inside the route and leave those
routes untested, which keeps each listing short. Use the pattern
above whenever a route that needs `js` also needs a test.

## Recipe: touching the live page

`js.document` can find an element of the page that is showing and
change it directly. Give a component an `id` keyword, find its
element with `js.document.getElementById`, and then change the
element.

The demos in this documentation all share one Python with the
documentation page around them, so `js.document` on this page would
be the documentation page and not the demo. Most of the remaining
recipes are therefore shown as listings without a demo. Each
listing is a complete program that was run in a browser. Save it as
a file and run it to try it.

```python
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Roll Call"),
        Div("Ada the corgi", id="ada"),
        Div("Babbage the small black mutt", id="babbage"),
        Div("Captain the grey cat", id="captain"),
        Button("Find Babbage", "find_babbage")
    ])


@route
def find_babbage(state: State) -> Update:
    import js
    row = js.document.getElementById("babbage")
    row.style.background = "gold"
    return Update(state)


start_server(State())
```

Clicking the button gives Babbage's row a gold background. The
route returns [`Update(state)`](../reference/update.md) instead of
a `Page`. An `Update` stores the state and leaves the page on the
screen exactly as it is, including the change that the route made
by hand. If the route ended with `return index(state)`, Drafter
would rebuild the whole page from `index`, and the gold background
would be gone again at once. A rebuild also empties any text box
that the visitor was typing in, which is a second reason to return
an `Update` after a small change.

The same three steps work for other things an element can do.
`row.scrollIntoView()` scrolls the page until the element is
visible, and calling `focus()` on a text box's element puts the
cursor in it. A `TextBox("visitor")` has the id `visitor`, so
`js.document.getElementById("visitor")` finds it without an `id`
keyword.

### Waiting for a JavaScript promise

Some browser functions do not finish right away. Copying to the
clipboard, asking for a permission, and fetching a file each
return a **promise**, which is JavaScript's object for a result
that will arrive later. JavaScript code waits for a promise with a
keyword named `await`, and Python has the same keyword for its own
`async def` functions.

A Drafter route cannot wait that way. A route must be a regular
function that returns its page as soon as it is called. A route
written with `async def` produces an error page titled "Route Did
Not Return a Page", which reports that the route returned a
coroutine instead of a `Page`.

What does work is to give the promise a function to call when the
result arrives. Every promise has a `then` method for that purpose.

```python
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    code: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Your Invitation"),
        "Share this code with a friend: " + state.code + "\n",
        Button("Copy the code", "copy_code"),
        Span("", id="status")
    ])


@route
def copy_code(state: State) -> Update:
    import js

    def show_copied(result):
        js.document.getElementById("status").textContent = " Copied!"

    def show_refused(error):
        js.document.getElementById("status").textContent = " Could not copy."

    js.navigator.clipboard.writeText(state.code).then(show_copied, show_refused)
    return Update(state)


start_server(State("CORGI-2026"))
```

`writeText` starts the copy and returns a promise. `then` takes two
functions. The browser calls the first one if the promise succeeds
and the second one if it fails, for example because the browser
refused access to the clipboard. Each function receives one
argument, which is the result or the error.

The route does not wait for either function. It returns its
`Update` immediately, and the browser calls one of the two
functions a moment later. No route is running by then, so the
function has no page to return. It changes the live page directly,
as the previous recipe did, by writing a message into the empty
`Span`.

Sometimes a later route needs the value that a promise produced.
In that case, have the function put the value into a text box by
assigning to the element's `value`. The value then reaches a route
as a parameter when the visitor presses a button, like anything
else that is typed into a form.

Pyodide also has a function named `run_sync`, imported from
`pyodide.ffi`, which pauses a route until a promise finishes and
returns the result. `response = run_sync(js.fetch("index.html"))`
worked in Chromium, the engine behind Chrome and Edge, when this
page was tested. Pyodide's documentation says that `run_sync`
depends on a browser feature that is not available everywhere, so
test it in every browser your visitors might use, and treat `then`
as the dependable choice.

## Recipe: shipping JavaScript with a page

Sometimes the code you want is already written in JavaScript. It
might be a short snippet from a tutorial or a whole library. Drafter
can deliver JavaScript to the browser with one page or with the
whole site.

### JavaScript for one page

[`Page`](../reference/page.md) accepts a `js` keyword that holds
JavaScript code as a string. Drafter runs the code every time that
page is shown, after the page's content is in place. This to-do
list uses one line of JavaScript to put the cursor back in the text
box after each addition, so that the visitor can keep typing. It is
shown without a demo because a demo that takes the cursor would
pull this page away from the paragraph you are reading.

```python
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    tasks: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("To-Do"),
        BulletedList(state.tasks),
        TextBox("new_task"),
        Button("Add", "add_task")
    ], js="document.getElementById('new_task').focus();")


@route
def add_task(state: State, new_task: str) -> Page:
    state.tasks.append(new_task)
    return index(state)


assert_state(add_task(State([]), "walk Ada"), State(["walk Ada"]))

start_server(State([]))
```

In JavaScript, `document` is the page, which is the same object
that Python reaches as `js.document`. The JavaScript is an ordinary
string as far as Python is concerned, so the test runs on your
computer without any trouble. `Page` also accepts a `css` keyword,
which adds a string of CSS for as long as that page is showing.

### JavaScript for the whole site

Two functions add JavaScript to every page. Call them near the top
of your program, before `start_server`.

- `add_website_js("...")` takes JavaScript code as a string and
  runs it once, when the site first loads and before the first page
  appears.
- `add_website_js_file("app.js")` loads a JavaScript file. The
  argument is the name of a `.js` file next to your program, or a
  full web address.

The [site configuration reference](../reference/site-config.md#add_website_js)
describes both functions. Three of the sections below use them.

### Loading a library from a CDN

A CDN is a web server that hosts copies of popular JavaScript
libraries for any site to load. This program loads a small library
named canvas-confetti and uses it to throw confetti across the
page.

```python
from drafter import *
from dataclasses import dataclass

add_website_js_file(
    "https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"
)


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adoption Day"),
        "Domino the black cat has a new home.\n",
        Button("Celebrate", "celebrate")
    ])


@route
def celebrate(state: State) -> Update:
    import js
    js.confetti()
    return Update(state)


start_server(State())
```

The library defines one JavaScript function named `confetti`.
Every name that a JavaScript library defines for the whole page is
also an attribute of the `js` module, so the route calls the
function as `js.confetti()`. The `@1.9.3` in the address asks for
one exact version of the library, so the file cannot change after
you have tested with it.

Two cautions apply to any library loaded this way.

- The browser fetches the library in the background while your
  first page is being built. A route that runs after a click can
  rely on the library. The `index` route cannot rely on it the
  first time it runs, and calling `js.confetti()` there produces an
  error page titled "Missing Attribute".
- A site that loads a library from a CDN needs an internet
  connection, and it needs the CDN to keep hosting the file. To
  remove both needs, download the file, save it next to your
  program, and pass its name instead of the address, as in
  `add_website_js_file("confetti.browser.min.js")`. Drafter then
  copies the file into your site when you deploy it.

### Calling a route from JavaScript

Drafter gives every `Button` and `Link` an HTML attribute named
`data-nav`, whose value is the name of the route to run. Drafter
watches for clicks on those elements. JavaScript can therefore run
a route by finding the right button and clicking it. In this
program, pressing the right arrow key does the same thing as
clicking **Next**. Click inside the demo once before you press the
key, so that the demo receives your typing.

```python drafter height=360
from drafter import *
from dataclasses import dataclass

add_website_js("""
if (!window.cardKeysReady) {
    window.cardKeysReady = true;
    document.addEventListener("keydown", function (event) {
        if (event.key === "ArrowRight") {
            var button = document.querySelector('[data-nav="next_card"]');
            if (button) {
                button.click();
            }
        }
    });
}
""")


@dataclass
class State:
    cards: list[str]
    position: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Flash Cards"),
        state.cards[state.position] + "\n",
        Button("Next", "next_card"),
        "\nThe right arrow key also shows the next card."
    ])


@route
def next_card(state: State) -> Page:
    state.position = (state.position + 1) % len(state.cards)
    return index(state)


assert_state(next_card(State(["one", "two"], 1)), State(["one", "two"], 0))

start_server(State([
    "Ada is a corgi.",
    "Babbage is a small black mutt.",
    "Captain is a grey cat.",
    "Domino is a black cat."
], 0))
```

The JavaScript reads as follows.

- `document.addEventListener("keydown", ...)` asks the browser to
  call the function that follows whenever a key is pressed.
- `document.querySelector('[data-nav="next_card"]')` finds the
  element whose `data-nav` is `next_card`, which is the **Next**
  button.
- `button.click()` presses the button. Drafter then runs
  `next_card` exactly as if the visitor had clicked, and the values
  of any text boxes on the page are sent to the route as usual.
- `if (button)` skips the click on a page that has no such button.
- The two lines about `window.cardKeysReady` make sure that the
  listener is added only once. While you are developing, each save
  reloads your program and runs this JavaScript again. Without the
  check, a second listener would make one key press count twice.

A button does not have to be visible for this to work.
`Button("Next", "next_card", style_display="none")` hides the
button from the visitor, and JavaScript can still click it.

Use `data-nav` only to find buttons and links that Drafter made.
Writing the attribute on another element of your own, such as a
`<span>` inside `RawHTML`, does not make that element run a route.
A click on it only reports an error in the browser's console.

### Calling a Python function from JavaScript

JavaScript can also call a Python function directly, without going
through a route. The `then` method above is one case. Many other
JavaScript functions accept a function to call later, and for
those the Python function has to be wrapped first.

```python
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Dinner Bell"),
        Div("Domino the black cat is napping.", id="bell"),
        Button("Remind me in three seconds", "set_reminder")
    ])


@route
def set_reminder(state: State) -> Update:
    import js
    from pyodide.ffi import create_once_callable

    def ring():
        js.document.getElementById("bell").textContent = "Time to feed Domino!"

    js.setTimeout(create_once_callable(ring), 3000)
    return Update(state)


start_server(State())
```

`js.setTimeout` is the browser's function for calling something
after a delay, which is given in thousandths of a second.
`create_once_callable` wraps a Python function that JavaScript will
call exactly once. Its relative `create_proxy`, also in
`pyodide.ffi`, wraps a function that will be called many times,
such as one passed to `addEventListener`. The wrapping keeps the
Python function alive after the route has returned. An unwrapped
function fails when the browser tries to call it, with an error in
the browser's console that begins "This borrowed proxy was
automatically destroyed".

A function called this way runs outside any route, so it receives
no state and returns no page. It can change the live page, as
`ring` does. If it needs to change the state, have it click a
button, as in the previous section, so that a route does the work.
For behavior on a timer in a real project, the
[Timer](../reference/components/time/timer.md) component is the
better tool, because it calls a route for you.

### Running JavaScript after every page

Each time Drafter finishes showing a page, it sends the browser
window an event named `drafter-page-loaded`. A script for the whole
site can listen for that event in order to do something after
every page. The event's `detail.route` holds the name of the route
that produced the page.

```python
add_website_js("""
window.addEventListener("drafter-page-loaded", function (event) {
    document.title = "Pet Hotel: " + event.detail.route;
});
""")
```

With these lines near the top of a program, the browser tab reads
"Pet Hotel: index" on the first page, and the name after the colon
changes with each page that follows. Drafter does not send the
event after an `Update`, because no page was shown.

## Custom elements exist

Drafter's own interactive components, such as Timer, Map, and
Camera, are custom HTML elements written in TypeScript. Each one is
paired with a Python class that declares the events it can send to
a route. Building one means contributing to the library itself,
which is a larger job than anything else on this page.
[Build your own components](custom-components.md) covers what you
can build in Python alone, and the
[developer documentation](../dev/index.md) covers the rest.

## Common problems

- **`ModuleNotFoundError: No module named 'js'`.** An `import js`
  ran on your computer. Either the import is at the top of the
  file, or a test called a route that contains it. Move the import
  inside the route, and see
  [One file, two places](#one-file-two-places) for a route that
  also needs a test.
- **An error page titled "Missing Attribute" that mentions
  `JsNull`.** `getElementById` found no element with that id.
  JavaScript's value for "nothing" appears in Python as `JsNull`,
  which is not the same as `None`, so `if row is None` never
  catches it. Check the spelling of the id, and write `if row:`
  when you need to test whether an element was found.
- **The change disappeared at once.** The route returned a `Page`,
  and the rebuild replaced the element that you changed. Return
  `Update(state)` after changing the page by hand.
- **"Route Did Not Return a Page" from a route that uses `await`.**
  A route cannot be an `async def` function. Use `then`, as in
  [Waiting for a JavaScript promise](#waiting-for-a-javascript-promise).
- **A library's function is missing on the first page.** A library
  added with `add_website_js_file` is still loading while `index`
  runs for the first time. Call the library from a route that a
  button triggers.
- **One key press acts twice while you are developing.** Each save
  ran your site-wide JavaScript again and added another listener.
  Add a check like the `cardKeysReady` lines above, and refresh the
  browser tab to clear the extra listeners.
- **Deciding what to keep from a `js` value.** Numbers and text
  from JavaScript are ordinary Python values and can go into your
  state. An element or any other JavaScript object is a wrapper
  that exists only in the browser tab. Read the numbers or text
  that you need from the wrapper, and keep those.

## Related

- [Python in the browser](pyodide.md) explains why the same file
  runs in two places.
- [Site configuration functions](../reference/site-config.md) is
  the reference for `add_website_js` and `add_website_js_file`.
- [Update](../reference/update.md) describes the response that
  leaves the page on screen as it is.
- [Canvas](../reference/components/media/canvas.md) draws on a
  canvas element with the steps from the live page recipe.
- [Pyodide's guide to the js module](https://pyodide.org/en/stable/usage/type-conversions.html)
  describes how values are converted between Python and
  JavaScript.

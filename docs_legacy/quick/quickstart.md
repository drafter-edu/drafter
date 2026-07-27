## Quick Start New: A Carefully Guided Counter

This guide introduces Drafter slowly, one idea at a time.

You will learn:

- `start_server(...)`
- `@route`
- `Page(...)`
- `State` with a dataclass

## 0. Start The Server

The most important first step is starting the server.

```python drafter
from drafter import *


start_server()
```

`start_server()` launches your site so you can visit it in a browser.

At this point, Drafter gives you a default page. We have not written any routes yet, so the site is just the starting point.

## 1. Add One Route

Now create a route named `index`. This is usally your main page and all drafter projects/websites should have at least the `index` route.

```python drafter
from drafter import *


@route
def index() -> Page:
    return Page([
        "Hello from Drafter!"
    ])


start_server()
```

What this means:

- `@route` turns a function into a web page.
- `index` is the main page of the site.
- `Page([...])` gives the content to show.

## 2. Add A Little More Content

A `Page` is a way to show and organize information. The content inside a `Page` is just a list. These items can be strings or as you'll see shortly components such as buttons. The items appear in the order you list them.

```python drafter
from drafter import *


@route
def index() -> Page:
    return Page([
        "This is a simple Drafter page.",
        "Strings become text on the page."
    ])


start_server()
```

## 3. Introduce State

State is how your app remembers information.

We will use a counter, because it is easy to see state changing. State is simply a dataclass that you define in our example we gave our State dataclass a count field, that tracks a number. 

```python drafter
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    count: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current count: " + str(state.count)
    ])


start_server(State(0))
```

Here, the `State(0)` value passed to `start_server(...)` is the initial value for `count`.

That means when the app first opens, `state.count` starts at `0`.

## 4. See Different Initial Values

You can start the same app with a different initial state value.

```python drafter
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    count: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current count: " + str(state.count)
    ])


start_server(State(10))
```

If you use `State(10)`, then the counter starts at `10` instead of `0`.

This is the connection to remember:

- `State(...)` creates the starting data.
- `start_server(...)` receives that starting data.
- The first page sees that starting data as its `state`.

## 5. Add Buttons That Change State

Before we use buttons, it helps to know the syntax.

```python
Button(text, route)
```

- The first parameter is the button label, the text the user sees.
- The second parameter is the route function the button runs when clicked.

For example, `Button("+1", increment)` means the button will show `+1` and run the `increment` route.

Now let the user change the counter.

```python drafter
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    count: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Current count: " + str(state.count),
        Button("+1", increment),
        Button("-1", decrement),
        Button("Reset", reset_count)
    ])


@route
def increment(state: State) -> Page:
    state.count += 1
    return index(state)


@route
def decrement(state: State) -> Page:
    state.count -= 1
    return index(state)


@route
def reset_count(state: State) -> Page:
    state.count = 0
    return index(state)


start_server(State(0))
```

What is happening here:

- The buttons go to other routes.
- Those routes change `state.count`.
- The page is then shown again with the updated value.

## 6. Try It Next

- Change `State(0)` to `State(5)` and see the first page change.
- Add a `+5` button.
- Prevent the counter from going below `0`.

The key idea is simple: routes show pages, state remembers values, and `start_server(...)` begins the app with an initial state.

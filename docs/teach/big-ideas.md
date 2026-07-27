---
page_type: concept
title: The big ideas
audience: T
priority: P1
prereqs: []
symbols: []
outcome: Know what to emphasize when teaching.
search:
  exclude: true
---

# The big ideas

## In one sentence

Nine ideas carry all of Drafter; teach them in this order and
everything else is detail.

## The idea

Each idea below names the concept, the canonical student page for
it, and what to emphasize. The guided projects introduce them in
roughly this order, always behavior first, vocabulary second.

1. **A route is a function that returns a page.**
   ([Routes and pages](../concepts/routes-and-pages.md)) The single
   most load-bearing idea, and the most commonly garbled. A route
   is not a page; it is a function that builds and returns one,
   the way a recipe is not a cake. Students who hold this
   distinction can reason about parameterized and conditional
   pages; students who lose it treat routes as static documents.
2. **Buttons and links name the route to call.**
   ([Button](../reference/components/actions/button.md)) A
   `Button("Feed", "feed")` connects to the route by its name as a
   string. Clicking means calling that function.
3. **State is one dataclass, threaded through every route.**
   ([State](../concepts/state.md)) Routes receive the state, may
   change its fields, and pass it into the returned page. This is
   the course's mutation-and-aliasing story in a context where it
   visibly matters.
4. **Form fields become parameters, matched by name.**
   ([Forms and input](../concepts/forms-and-input.md)) A
   `TextBox("color")` submits its value to a parameter named
   `color`. The name contract is where most early form bugs live.
5. **Type annotations drive conversion.** Form values arrive as
   text unless the parameter's annotation says otherwise;
   `guesses: int` is a meaningful, load-bearing annotation, not
   decoration.
6. **Pages can differ because state differs.**
   ([Dynamic pages](../concepts/dynamic-pages.md)) Conditionals
   and loops inside routes, helper functions that return
   components, one route serving many items.
7. **Routes are testable functions.**
   ([Test a feature](../add/test-a-feature.md)) Build a state,
   call the route, assert. Worth modeling constantly in lecture,
   not saving for a testing week.
8. **The program runs twice, and there is no server.**
   ([How Drafter works](../start/how-drafter-works.md)) Once on
   the student's computer (startup and tests), once in the
   browser where the real app lives. State is in memory and lost
   on reload; nothing is secret or secure.
9. **Deployment is compilation.**
   ([Deploy and submit](../your-project/deploy/index.md)) The app
   becomes static files; GitHub Pages serves them. No server to
   administer, and also no server to store anything on.

## See it

Ideas 1 through 7 fit in one small program, which makes it a good
running lecture example:

```python drafter height=320
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    treats: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Captain's Treat Counter"),
        "Treats given: " + str(state.treats) + "\n",
        TextBox("amount", "1"),
        "\n",
        Button("Give treats", "give")
    ])


@route
def give(state: State, amount: int) -> Page:
    state.treats = state.treats + amount
    return index(state)


assert_state(give(State(0), 3), State(3))

start_server(State(0))
```

One route builds the page from state (ideas 1, 3), the button
names the `give` route (2), the text box's name matches the
`amount` parameter (4), the `int` annotation converts it (5), the
page text varies with state (6), and the assertion tests the route
by calling it (7).

## What this means for your code examples

- Say "the route that builds the page", never "the page's code".
  Small phrasing choices either reinforce idea 1 or erode it.
- Thread state visibly: examples where a change on one page shows
  up on another page make idea 3 concrete faster than any diagram.
- Put one assertion in every example you show, from the first
  week you use Drafter.
- Keep examples inside the known-constructs set (functions,
  dataclasses, lists, loops); the student docs never assume more.

## Where people get confused

Every idea above has a matching failure mode in
[Student misconceptions](student-misconceptions.md), with symptoms
and repair moves. The two most consequential: believing the app
runs on a remote server (idea 8), and believing the browser's back
button undoes the last action rather than replaying a route.

## Go deeper

- [Concepts index](../concepts/index.md): the student-facing
  concept ladder these map onto.
- [Beyond the student docs](beyond-the-basics.md): what to teach
  students who outrun the spine.

---
page_type: index
title: Drafter
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Understand what Drafter is and take the right next step.
hide:
  - navigation
  - toc
---

# Drafter

<div class="drafter-home" markdown>

<div class="drafter-home__main" markdown>

<div class="drafter-hero" markdown>

**Drafter turns the Python you already know into real, interactive
websites.** Write plain functions, decorate them with `@route`, and Drafter
serves the pages they return as a website you can click through, test, and
publish for free.

```python drafter height=180
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    clicks: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "You have clicked " + str(state.clicks) + " times.\n",
        Button("Click me!", "add_click"),
    ])


@route
def add_click(state: State) -> Page:
    state.clicks = state.clicks + 1
    return index(state)


start_server(State(0))
```

That is a complete Drafter program. Try clicking the button above, then
change the code and run it again.

</div>

</div>

<aside class="drafter-home__side" markdown>

<div class="grid cards" markdown>

- **Start here**

    ---

    Never used Drafter? Build your first working site in about twenty
    minutes.

    [Go to Start](start/index.md)

- **Guided Projects**

    ---

    Build a virtual pet, a story maker, and a quiz game.

    [See the projects](tutorials/index.md)

- **Find a component**

    ---

    Look up buttons, forms, tables, maps, cameras, and more.

    [Browse the reference](reference/components/index.md)

</div>

## Working on your project?

- [Choose a manageable idea](your-project/choose-an-idea.md)
- [Plan your pages and data](your-project/sketch-the-pages.md)
- [Build and test one path](your-project/build-one-path.md)
- [Deploy and submit](your-project/deploy/index.md)
- [Browse the project gallery](your-project/gallery/index.md)

## Need one thing?

- [Add a feature to your app](add/index.md)
- [Look up a component](reference/components/index.md)
- [Fix an error](help/errors/index.md)
- [Get help](help/index.md)

<p class="drafter-home__quiet" markdown>
Teaching a course? See the [instructor documentation](teach/index.md).
Contributing to Drafter? See the [developer documentation](dev/index.md).
</p>

</aside>

</div>

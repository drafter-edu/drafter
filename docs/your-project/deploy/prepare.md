---
page_type: how-to
title: Prepare for release
level: L2
audience: S
priority: P0
prereqs: [your-project/deploy]
symbols: []
outcome: Make the app production-ready.
---

# Prepare for release

## Goal

You want your app ready for the public, with a proper title, an about
page, no debug panel, and the full width of the screen.

## Before you start

Your app works locally. All of the changes on this page are a handful of
configuration lines. Put them **after your imports and before your
routes**, and test locally before publishing.

## The release block

Four calls turn a practice app into a releasable one:

```python
set_website_title("Corgi Cafe")
set_site_information(
    author="Your Name",
    description="Order snacks for very good dogs.",
    sources="Thanks to the Drafter docs and my study group.",
    planning="plan.pdf",
    links=["https://github.com/your-username/your-repository"]
)
hide_debug_information()
set_website_framed(False)
```

What each line does:

- `set_website_title(...)` sets the title shown in the browser tab.
- `set_site_information(...)` fills your site's **about page**: who made
  it, what it does, what sources helped, any planning document you
  bundled, and related links. All five fields are required; use an empty
  string (or empty list for `links`) for any that do not apply. Visitors
  reach the page at your site's address plus `--about`. The values can
  be strings, lists of strings, or components like `Link`.
- `hide_debug_information()` removes the debug panel, so visitors see
  only the app itself.
- `set_website_framed(False)` lets the app fill the whole browser window
  instead of the small development frame.

## See it running

Here is a small finished app with its release block. Notice that the
debug panel no longer appears below the page.

```python drafter height=260
from drafter import *
from dataclasses import dataclass

set_website_title("Corgi Cafe")
set_site_information(
    author="A. Student",
    description="Order snacks for very good dogs.",
    sources="",
    planning="",
    links=[]
)
hide_debug_information()


@dataclass
class State:
    snacks_served: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Corgi Cafe"),
        "Snacks served to Ada so far: " + str(state.snacks_served) + "\n",
        Button("Serve a snack", "serve")
    ])


@route
def serve(state: State) -> Page:
    state.snacks_served = state.snacks_served + 1
    return index(state)


assert_state(serve(State(0)), State(1))

start_server(State(0))
```

## While you are still working

Comment out the `hide_debug_information()` line until you are actually
done, so that you keep the debugger while you are still debugging:

```python
# hide_debug_information()
```

Uncomment it as the last edit before publishing.

## A quick pre-flight check

Run the app locally one more time and confirm:

- The tab shows your title.
- The debug panel is gone.
- Your tests still print `SUCCESS` in the console.
- Every image or data file your app opens sits next to your program
  file, because it must be uploaded along with it
  ([missing files 404 after deploy](../../help/errors/missing-asset-on-deploy.md)).

## Common problems

- **The debug panel is still there**: `hide_debug_information()` must
  run before `start_server(...)`, and must not be commented out.
- **The about page is empty**: `set_site_information(...)` was not
  called, or runs after `start_server(...)`. Configuration goes near the
  top of the file.
- **The app is still in a small box**: add `set_website_framed(False)`.
- **You cannot debug anymore**: that is the expected effect of hiding
  the debug information. Comment the line out while you are still
  developing.

## Understand it

Configuration calls change how the site presents itself, never what it
does. [How Drafter works](../../start/how-drafter-works.md) explains
why.

## See another example

[Finish and test an app](../../tutorials/finishing.md) walks this same
preparation on a guided project.

## Look it up

[Site configuration](../../reference/site-config.md) lists every `set_`
and `add_` function, including favicons and custom error pages.

## Fix a problem

[Fix a failed deployment](troubleshooting.md) if problems appear after
publishing.

## Next steps

Your app is ready, but **you are not done yet**: right now it is only
ready on your own computer. Publishing is next.

<div class="grid cards" markdown>

- **Step 2 of 3: Publish on GitHub Pages**

    ---

    Upload your code, flip one setting, run the workflow, and get your
    URL.

    [Publish on GitHub Pages](github-pages.md)

</div>

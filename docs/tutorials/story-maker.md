---
page_type: tutorial
title: 2. Build a story maker
level: L2
audience: S
priority: P0
prereqs: [tutorials/virtual-pet]
symbols: []
outcome: Build a multi-page app where form values cross pages.
---

# 2. Build a story maker

## What you'll build

You will build a fill-in-the-blank story maker. One page asks for a hero,
a place, and an object, and the next page weaves them into a story.
Changing one word changes the whole story, and the same three words can
tell more than one story.

## Try the finished app

Fill in the blanks, tell the story, then tell it differently without
retyping anything:

```python drafter height=380
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hero: str
    place: str
    thing: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Fill in the blanks, then tell the story.\n",
        "A hero:",
        TextBox("hero", state.hero),
        "\nA place:",
        TextBox("place", state.place),
        "\nAn object:",
        TextBox("thing", state.thing),
        "\n",
        Button("Tell the story", "story")
    ])


@route
def story(state: State, hero: str, place: str, thing: str) -> Page:
    state.hero = hero
    state.place = place
    state.thing = thing
    return Page(state, [
        "Long ago, " + state.hero + " traveled to " + state.place + ".",
        "Nobody there had ever seen " + state.thing + " before.",
        "By sunset, " + state.hero + " was famous.\n",
        Button("Tell it differently", "another_story"),
        Button("Change the words", "index")
    ])


@route
def another_story(state: State) -> Page:
    return Page(state, [
        "Deep in " + state.place + ", something glittered.",
        "It was " + state.thing + ", lost for a hundred years.",
        "Only " + state.hero + " knew what it could do.\n",
        Button("Tell the first story", "story_again"),
        Button("Change the words", "index")
    ])


@route
def story_again(state: State) -> Page:
    return story(state, state.hero, state.place, state.thing)


start_server(State("Ada", "the library", "a tiny robot"))
```

**Before building it, answer from playing**: when you click "Change the
words", the boxes are already filled in with your words. Where must those
words be stored for that to work?

## What you need

- The virtual pet finished, or comfort with state, routes, and buttons.
- One sitting.

## Step 1: Ask, then answer

Start with the smallest version of the contract you met in
[Forms and input](../concepts/forms-and-input.md): one page asks for a
value, and one route receives it. Watch the name `hero` travel from the
`TextBox`, through the button click, into the parameter:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hero: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "Who is the hero of the story?",
        TextBox("hero"),
        "\n",
        Button("Tell the story", "story")
    ])


@route
def story(state: State, hero: str) -> Page:
    state.hero = hero
    return Page(state, [
        "Once upon a time, there was " + state.hero + ".\n",
        Button("Start over", "index")
    ])


start_server(State(""))
```

The route saves `hero` into state right away. A parameter only exists
during the call that receives it, but state lasts from page to page.

## Step 2: Three blanks, three parameters

A page can hold several inputs. When the button is clicked, all of them
are delivered to the target route, each matched to the parameter with the
same name:

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hero: str
    place: str
    thing: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "A hero:",
        TextBox("hero"),
        "\nA place:",
        TextBox("place"),
        "\nAn object:",
        TextBox("thing"),
        "\n",
        Button("Tell the story", "story")
    ])


@route
def story(state: State, hero: str, place: str, thing: str) -> Page:
    state.hero = hero
    state.place = place
    state.thing = thing
    return Page(state, [
        "Long ago, " + state.hero + " traveled to " + state.place + ".",
        "Nobody there had ever seen " + state.thing + " before.",
        "By sunset, " + state.hero + " was famous.\n",
        Button("Change the words", "index")
    ])


start_server(State("", "", ""))
```

**Predict first**: rename the first `TextBox` to `"heroine"` but leave the
parameter called `hero`. What will happen when you click the button? Try
it, read the error, then change both names to match.

## Step 3: Remember the words

Try the Step 2 app again and notice a small annoyance: when you come back
to change the words, the boxes are empty. The fix uses an idea you
already know from the pet. The words are stored in state, so pass each
one to its `TextBox` as the starting value.

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hero: str
    place: str
    thing: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "A hero:",
        TextBox("hero", state.hero),
        "\nA place:",
        TextBox("place", state.place),
        "\nAn object:",
        TextBox("thing", state.thing),
        "\n",
        Button("Tell the story", "story")
    ])


@route
def story(state: State, hero: str, place: str, thing: str) -> Page:
    state.hero = hero
    state.place = place
    state.thing = thing
    return Page(state, [
        "Long ago, " + state.hero + " traveled to " + state.place + ".",
        "Nobody there had ever seen " + state.thing + " before.",
        "By sunset, " + state.hero + " was famous.\n",
        Button("Change the words", "index")
    ])


start_server(State("Ada", "the library", "a tiny robot"))
```

Now the app has a pleasant loop: you tell the story, tweak one word, and
tell it again. Giving `State` real starting values also means the first story
works before the visitor types anything.

## Step 4: A second story from the same words

The words live in state, so another route can tell a different story
without any new typing. `another_story` takes no extra parameters because
it needs nothing from the page; everything it uses comes from state. Add
tests for both story routes while you are here:

```python drafter height=400
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hero: str
    place: str
    thing: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "A hero:",
        TextBox("hero", state.hero),
        "\nA place:",
        TextBox("place", state.place),
        "\nAn object:",
        TextBox("thing", state.thing),
        "\n",
        Button("Tell the story", "story")
    ])


@route
def story(state: State, hero: str, place: str, thing: str) -> Page:
    state.hero = hero
    state.place = place
    state.thing = thing
    return Page(state, [
        "Long ago, " + state.hero + " traveled to " + state.place + ".",
        "Nobody there had ever seen " + state.thing + " before.",
        "By sunset, " + state.hero + " was famous.\n",
        Button("Tell it differently", "another_story"),
        Button("Change the words", "index")
    ])


@route
def another_story(state: State) -> Page:
    return Page(state, [
        "Deep in " + state.place + ", something glittered.",
        "It was " + state.thing + ", lost for a hundred years.",
        "Only " + state.hero + " knew what it could do.\n",
        Button("Change the words", "index")
    ])


assert_has(story(State("", "", ""), "Ada", "the moon", "a spoon"), "Ada traveled to the moon")
assert_state(story(State("", "", ""), "Ada", "the moon", "a spoon"), State("Ada", "the moon", "a spoon"))
assert_has(another_story(State("Ada", "the moon", "a spoon")), "Deep in the moon")

start_server(State("Ada", "the library", "a tiny robot"))
```

Read the tests as sentences. The first says that telling the story with
these three words should produce a page containing "Ada traveled to the
moon". The second says that the same call should leave those words saved
in state. The third says that `another_story` should build its page from
state alone.

## Common problems

- **An error about a missing parameter**: an input's name and the route's
  parameter name do not match. The error names the parameter it expected;
  compare it with your `TextBox(...)` names letter by letter.
- **A "points to non-existent page" error**: a button names a route that
  does not exist yet. Check spelling, and make sure the route has
  `@route` above it.
- **The boxes come back empty**: each `TextBox` needs its starting value,
  like `TextBox("hero", state.hero)`, and the story route must save its
  parameters into state first.
- **Your story shows blank spots**: the visitor left a box empty. That is
  allowed; decide whether your starting values make that impossible or
  whether a blank hero is funny enough to keep.

## Name it

- The pages that collect input are **forms**, and the values they carry
  are delivered as **parameters**. The full contract, including how types
  are converted, is described in
  [Forms and input](../concepts/forms-and-input.md).
- Moving between `index`, `story`, and `another_story` is **navigation**:
  buttons name routes, and routes return pages, as
  [Routes and pages](../concepts/routes-and-pages.md) explains.

## Make it yours

1. Add a fourth blank (an animal, a food, a feeling) and thread it
   through both stories.
2. Write a third story template, and a button on each story page leading
   to it.
3. Make the story change based on the words: if the hero's name is short,
   use a nickname sentence. Write a test for it.
4. Harder: add a `TextBox("years", 100)` and an `int` parameter, and put
   the number in a sentence. What happens if the visitor types `abc`?

## Next steps

You unlocked two task pages:
[Ask the user for information](../add/ask-for-information.md) covers
every input component, and
[Add and connect pages](../add/pages.md) covers linking pages.

<div class="grid cards" markdown>

- **Next project: Make a quiz game**

    ---

    A list of questions drives the pages: one route serves every
    question and keeps a running score.

    [Make a quiz game](quiz-game.md)

</div>

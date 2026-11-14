---
page_type: how-to
title: Build your own components
level: L4
audience: S
priority: P2
prereqs: [extend/javascript]
symbols: []
outcome: Create reusable components.
---

# Build your own components

## Goal

Package a piece of a page that you keep rebuilding, so that you
can use it the way you use a built-in component. There are three
levels, and the first one covers almost every project.

## Before you start

You can build pages comfortably, and you have written the same
group of components at least twice. Each level is more powerful
than the one before it and also harder to get right, so start at
level 1 and move up only when a level cannot express what you
need.

## Level 1: a function that returns components

A component of your own can be a function that returns the
content you keep writing. The function takes parameters like any
other, and its result can go anywhere content can go, including
inside another component.

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


def PetCard(name: str, species: str, motto: str) -> PageContent:
    return Div(
        Header(name, 3),
        Emphasis(species),
        Paragraph('"' + motto + '"'),
        style_border="2px solid #888",
        style_padding="8px",
        style_margin="8px"
    )


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("The Residents"),
        PetCard("Ada", "corgi", "Every walk is the best walk."),
        PetCard("Captain", "grey cat", "I was here first."),
        PetCard("Domino", "black cat", "You saw nothing.")
    ])


assert_has(index(State()),
           PetCard("Ada", "corgi", "Every walk is the best walk."))

start_server(State())
```

Give these functions names that look like component names
(`PetCard` rather than `make_pet_card`), and have each one build
its result only from its parameters, without changing the state.
The test above the last line shows a benefit of this level: the
function returns ordinary components, so `assert_has` can look for
a whole card. Level 1 is enough for cards, banners, navigation
bars, and any other group of components that repeats.

## Level 2: RawHTML for markup no component makes

Sometimes the HTML you need has no component. If you need one
unusual tag around ordinary content, use `HtmlTag` and stay at
level 1. `HtmlTag("u", "Babbage")` wraps its content in whatever
tag you name, and the content is still escaped, which means that
any HTML inside it is shown as plain text instead of being run.
[Embed HTML](../add/html.md) shows `HtmlTag` in use.

If you need a block of markup written entirely by hand, a function
can return [RawHTML](../reference/components/media/rawhtml.md).
`RawHTML` sends your string to the browser exactly as you wrote it,
so Drafter's escaping no longer protects the page. The
[safety rule](../add/html.md#the-safety-rule) therefore applies in
full. Only text that you wrote yourself may go into the markup,
and text that a visitor typed must stay out.

```python
def Badge(label: str) -> PageContent:
    return RawHTML(
        '<span style="border-radius: 9px; background: gold; '
        'padding: 2px 8px;">' + label + "</span>"
    )
```

`Badge("Adopted")` is safe, because the label is your own text.
`Badge(new_name)`, where `new_name` came from a text box, would
break the rule, because any HTML the visitor typed would become
part of the page.

## Level 3: a real Component class

Every built-in component is a class that inherits from
`Component`, and you can write such a class yourself. A class of
your own gives you two things that a level 1 function cannot.
You decide which keywords become real HTML attributes, and the
component appears under its own name in test output. The cost is
that you are now working with Drafter's internal machinery, which
has more rules than the rest of the library.

The example builds a `FieldGroup`. It renders a `<fieldset>`,
the HTML element that draws a box around a group of form inputs
with a caption set into the top border. A fieldset can also be
switched off, which makes every input and button inside it stop
responding. Drafter has no fieldset component, and
`HtmlTag("fieldset", ...)` cannot switch one off, for a reason
explained below. A component class uses class variables and `*`
parameters, which your course may not have covered. The sections
after the example explain each one.

```python drafter height=540
from drafter import *
from drafter.components.page_content import ComponentArgument, RenderPlan
from dataclasses import dataclass


@dataclass
class State:
    applicant: str


@dataclass(repr=False)
class FieldGroup(Component):
    tag = "fieldset"
    caption: str
    content: list
    locked: bool

    ARGUMENTS = [
        ComponentArgument("caption"),
        ComponentArgument("content", kind="var", is_content=True),
        ComponentArgument("locked", kind="keyword", default_value=False),
    ]
    KNOWN_ATTRS = ["disabled"]
    RENAME_ATTRS = {"caption": "", "locked": "disabled"}

    def __init__(self, caption: str, *content, locked: bool = False,
                 **extra_settings):
        self.caption = caption
        self.content = list(content)
        self.locked = locked
        self.extra_settings = extra_settings

    def get_children(self, context) -> list:
        legend = RenderPlan(kind="tag", tag_name="legend",
                            children=[self.caption])
        return [legend] + self.content


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adopt Babbage"),
        "Latest applicant: " + state.applicant + "\n",
        FieldGroup(
            "Your application",
            "Your name: ",
            TextBox("visitor"),
            Button("Apply", "apply")
        ),
        FieldGroup(
            "Applications for Captain",
            "Captain the grey cat already has a home. ",
            Button("Apply", "apply"),
            locked=True
        )
    ])


@route
def apply(state: State, visitor: str) -> Page:
    state.applicant = visitor
    return index(state)


assert_has(index(State("nobody yet")),
           FieldGroup("Your application",
                      "Your name: ",
                      TextBox("visitor"),
                      Button("Apply", "apply")))
assert_state(apply(State("nobody yet"), "Grace"), State("Grace"))

start_server(State("nobody yet"))
```

The first group works like any other part of a form. The Apply
button in the second group does nothing when clicked, because that
group is locked.

### The class and its fields

`@dataclass(repr=False)` is the same decorator you put on `State`,
with one setting changed. The decorator makes two `FieldGroup`
values equal when their caption, content, and `locked` setting are
equal. `repr=False` tells the decorator to leave the printed form
alone, so that `Component` can print the component the way you
wrote it, as `FieldGroup('Your application', ...)`. That printed
form is what a failing test shows you.

`tag = "fieldset"` names the HTML element. The three annotated
lines after it declare the fields that each `FieldGroup` stores.

### ARGUMENTS and the constructor

`ARGUMENTS` lists the constructor's parameters in order, one
`ComponentArgument` for each. Drafter reads this list whenever it
prints, compares, or renders the component, so the list has to
match `__init__` exactly.

- `ComponentArgument("caption")` is an ordinary parameter that
  must be given.
- `kind="var"` marks the parameter that collects any number of
  values. It matches `*content` in `__init__`, where the `*` means
  "gather every remaining value into one group".
- `kind="keyword"` with a `default_value` marks an optional
  parameter that is given by name, as in `locked=True`.
- `is_content=True` says that the values are content to show
  inside the element. Arguments without it are settings.

`__init__` stores each value on `self` under the name used in
`ARGUMENTS`. The last parameter, `**extra_settings`, gathers every
other keyword into a dictionary, and every component must store
that dictionary as `self.extra_settings`. Styling keywords such as
`style_border` arrive there.

### How a setting becomes an HTML attribute

By default, Drafter turns every argument that is not content into
an HTML attribute with the same name as the field. Two class
variables and one list inside Drafter adjust that default, and
`FieldGroup` depends on all three.

`RENAME_ATTRS` maps a field name to the attribute name that should
be used instead. The field is called `locked` because that word
describes what the visitor experiences, and HTML calls the
attribute `disabled`, so the class maps `"locked"` to `"disabled"`.
Mapping a field to the empty string `""` leaves that field out of
the attributes altogether. The caption is shown in a `<legend>`
element inside the fieldset, not as an attribute, so the class
maps `"caption"` to `""`.

`KNOWN_ATTRS` lists the attributes that belong to this tag. Drafter
already recognizes the attributes that every tag accepts, such as
`id`, `title`, and `class`. Any other name is treated as a CSS
property and placed in the element's `style`. Without
`"disabled"` in `KNOWN_ATTRS`, the locked group would render as
`<fieldset style="disabled: True">`, which locks nothing. That
fallback is also why `HtmlTag("fieldset", ..., disabled=True)`
cannot lock a group.

`BOOLEAN_ATTRS` is a list inside Drafter rather than something your
class declares. It holds HTML's on-or-off attributes, among them
`disabled`, `checked`, `required`, `hidden`, and `open`. Drafter
writes an attribute from that list as a bare word when its value is
true and leaves it out when its value is false. As a result,
`locked=True` renders as `<fieldset disabled>` and not as
`<fieldset disabled="True">`.

The same rules apply to keywords that the caller adds. In
`FieldGroup("Pets", "Ada", title="Dogs first", width="50%")`, the
`title` becomes an attribute because every tag accepts one, and
`width` becomes the inline style `width: 50%` because Drafter does
not recognize it as an attribute of this tag.

### Children and the RenderPlan

`get_children` returns what goes inside the element. A
`RenderPlan` describes one HTML element that has no component of
its own, which here is the `<legend>` that holds the caption. The
content that the caller passed follows it. Text inside a
`RenderPlan` is escaped like all other content, so a caption that
contains HTML is shown as plain text.

Put together, the locked group produces this HTML. Drafter also
adds an `id` to the fieldset, and the button carries several
attributes of its own, which are left out here.

```html
<fieldset disabled>
  <legend>Applications for Captain</legend>
  Captain the grey cat already has a home.
  <button>Apply</button>
</fieldset>
```

### Testing the component

The two lines before `start_server` test the program the way you
would test any other. `assert_has` finds the first group in the
page, which works because two `FieldGroup` values with the same
arguments are equal. `assert_state` checks the `apply` route. When
a test like the first one fails, the message names the component
as `FieldGroup('Your application', ...)`, where a level 1 function
would be reported as the `Div` or `HtmlTag` it returned.

### Where to go from here

The built-in closest to `FieldGroup` is `Details`, in the file
`components/layout.py` of the Drafter source. It also places one
generated element ahead of the caller's content. `SelectBox`, in
`components/forms.py`, builds a list of `<option>` children from
its `options` field and maps that field to `""`. Beyond level 3
are interactive custom elements such as `Timer` and `Map`, which
pair a Python class with a part written in TypeScript. The
[developer architecture page](../dev/architecture.md) is the place
to start for those.

## Common problems

- **A level 1 function changes the state.** A function that
  changes state is doing a route's work. Pass the values in as
  parameters and return content, and leave state changes to the
  route that calls the function.
- **A test passes on text that no visitor can see.** A test
  treats a `RawHTML` value as one string that includes its tags
  and styles. `assert_has` matches it only against a `RawHTML`
  with the identical string, and a text search such as
  `assert_in("gold", page)` succeeds on the `Badge` above even
  though the word is part of a style. Level 1 components do not
  have this problem.
- **A level 3 field shows up as an inline style.** A style such
  as `style="caption: Your application"` means that a field which
  is not content was neither listed in `KNOWN_ATTRS` nor mapped in
  `RENAME_ATTRS`. Map the field to the right attribute name, or to
  `""` if it should not be an attribute at all.
- **A true-or-false keyword renders as `name="True"` or as a
  style.** The attribute needs to be in your `KNOWN_ATTRS`, and it
  is written as a bare word only if it is one of the attributes in
  Drafter's `BOOLEAN_ATTRS` list.
- **Level 3 takes more code than the result seems worth.** Check
  whether a level 1 function around existing components expresses
  the idea, which it usually does.

## Related

- [Embed HTML](../add/html.md) explains `HtmlTag`, `RawHTML`, and
  the safety rule that level 2 depends on.
- [Keywords every component accepts](../reference/keyword-attributes.md)
  lists the styling and attribute keywords that the caller of any
  component can add.
- [Developer documentation](../dev/index.md) covers the
  architecture and internals behind level 3.

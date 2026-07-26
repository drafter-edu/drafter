---
page_type: reference
title: Template zoo
audience: D
priority: P1
prereqs: []
symbols: []
outcome: Review every design-system element with dummy content.
search:
  exclude: true
---

# Template zoo

Every design-system element on one page, with dummy content, for visual and
accessibility review (STUDENT_DOCS_PLAN.md Phase C). This page renders in
the Developer zone; open any student page for the light/dark student
schemes and any Teach page for the navy scheme. The zone banner above is
the live one for this page.

## Page-type badges

The badge row at the top of this page is generated from front-matter. All
badge variants:

<p>
<span class="drafter-badge drafter-badge--type">Tutorial</span>
<span class="drafter-badge drafter-badge--type">Concept</span>
<span class="drafter-badge drafter-badge--type">How-to</span>
<span class="drafter-badge drafter-badge--type">Reference</span>
<span class="drafter-badge drafter-badge--type">Example</span>
<span class="drafter-badge drafter-badge--type">Troubleshooting</span>
</p>

## Level chips

<p>
<span class="drafter-badge drafter-badge--level">First steps</span>
<span class="drafter-badge drafter-badge--level">Core</span>
<span class="drafter-badge drafter-badge--level">Advanced</span>
<span class="drafter-badge drafter-badge--level">Specialized</span>
</p>

## Hero band (blueprint motif)

<div class="drafter-hero" markdown>

**A hero band.** The faint grid appears only here, in section-index
headers, and in empty-state illustrations, never behind body text.

</div>

## Embedded demo (drafting sheet)

```python drafter height=160
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    message: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "The zoo says: " + state.message,
        Button("Visit again", index),
    ])


start_server(State(message="hello"))
```

## Admonitions

!!! note "Note"
    A restrained note. Used for asides that most readers can skip.

!!! warning "Careful"
    A warning. Used when a likely action loses work or misleads.

!!! info "Deeper"
    A pointer to a deeper treatment on a concept or Extend page.

## Code block (static)

```python
from drafter import *

bold("This block is highlighted but not compiled into a demo.")
```

## Table

| Component | Group  | Level      |
| --------- | ------ | ---------- |
| Button    | Actions | Core       |
| Map       | Place  | Specialized |

## Cards

<div class="grid cards" markdown>

- **A card title**

    ---

    Card body text with a [link](../index.md).

- **Another card**

    ---

    Cards are used on index pages and for next-step navigation.

</div>

## Zone banners (static copies)

<div class="drafter-zone-banner drafter-zone-banner--teach">
  <span>Instructor documentation</span>
  <a href="../../start/">Students: go to the student docs</a>
</div>

<div class="drafter-zone-banner drafter-zone-banner--dev">
  <span>Developer documentation</span>
  <a href="../../reference/">Students: you probably want the Reference</a>
</div>

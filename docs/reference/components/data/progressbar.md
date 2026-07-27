---
page_type: component
title: ProgressBar
level: L3
audience: S
priority: P2
prereqs: []
symbols:
  - ProgressBar
outcome: Show progress.
---

# ProgressBar

Group: [Data display](../index.md#data-display)

## Description

A `ProgressBar` shows how far along something is: a quiz, a
loading step, a savings goal. It draws a filled bar proportional
to `value` out of `max`. For a measurement that is not progress
toward completion (a volume, a score in a range), use a
[Meter](meter.md) instead.

## Syntax

```python
ProgressBar(value)
ProgressBar(value, max)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `value` | number | required | How much is done. |
| `max` | number | `1.0` | The amount that counts as finished. With the default, `value` is a fraction like `0.75`. |

## Examples

```python drafter height=280
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    answered: int


TOTAL_QUESTIONS = 8


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet Trivia"),
        "Question " + str(state.answered + 1) + " of "
        + str(TOTAL_QUESTIONS) + "\n",
        ProgressBar(state.answered, TOTAL_QUESTIONS),
        "\n",
        Button("Answer it", "answer")
    ])


@route
def answer(state: State) -> Page:
    if state.answered + 1 >= TOTAL_QUESTIONS:
        return Page(state, [Header("Quiz complete!")])
    state.answered = state.answered + 1
    return index(state)


start_server(State(0))
```

## Notes

- Driving `value` from state, as above, is the whole pattern:
  every re-render draws the bar at the current amount.
- Whole numbers with a matching `max` (3 of 8) read more
  honestly than fractions for countable things.
- The bar alone is not enough information for everyone; pair it
  with text stating the numbers, as the example does.
- Colors and size come from the theme; styling keywords can
  adjust `style_width` and friends.

## Related components

- [Meter](meter.md): a gauge for measurements rather than
  completion.
- [Timer](../time/timer.md): for progress that advances by
  itself over time.

## External links

- [The progress element on MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/progress)

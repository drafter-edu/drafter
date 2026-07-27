---
page_type: component
title: Microphone
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Microphone
outcome: React to sound levels.
---

# Microphone

Group: [Sound](../index.md#sound)

## Description

A `Microphone` listens to how loud things are and calls routes
when the sound crosses a threshold: a clap starts the game, a
sustained shout fills a meter, silence ends the turn. It does
not record anything; it measures. (Recording is
[AudioRecorder](audiorecorder.md)'s job.) Like every
capture-style component, it starts with a permission prompt the
visitor can refuse.

## Syntax

```python
Microphone(name)
Microphone(name, threshold=0.6, on_loud="route_name")
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name; submitting the form delivers an [AudioLevel](../../data-types/audio-types.md) under it. |
| `threshold` | `float` | `0.5` | The loudness (0.0 to 1.0) that counts as "loud". |
| `cooldown` | `int` | `1000` | Minimum milliseconds between `on_loud` calls. |
| `rate` | `int` | `0` | Milliseconds between `on_level` calls, or 0 for never. |
| `show` | `bool` | `True` | Display the permission UI and live meter. |
| `visualize` | `str` | `"meter"` | The live display once granted: `"meter"`, `"waveform"`, or `"bars"`. |
| `on_loud` / `on_quiet` | `str` | none | Routes called when the volume rises past, and falls back below, the threshold. |
| `on_level` | `str` | none | Route called every `rate` milliseconds with the current volume. |
| `on_denied` / `on_error` | `str` | none | Routes for refusal and failure. |

## Examples

A noise meter for the classroom (or the dog):

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    barks: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Bark Counter"),
        Output("count", ["Barks detected: " + str(state.barks)]),
        "\n",
        Microphone("mic", threshold=0.6, cooldown=500,
                   on_loud="bark"),
        "\n",
        "Every loud noise counts as one bark. Ada disputes "
        "the methodology."
    ])


@route
def bark(state: State) -> Fragment:
    state.barks = state.barks + 1
    return Fragment(["Barks detected: " + str(state.barks)],
                    target="#count")


start_server(State(0))
```

## Notes

- The loud and quiet routes can receive `volume` (and the level
  route `volume` plus `peak_volume`) as float parameters by
  name.
- An event route that returns a whole `Page` re-renders the
  component, briefly resetting the meter and `peak_volume`;
  return an `Update` or a `Fragment` for frequent events.
- Tune `threshold` by watching the live meter, and use
  `cooldown` to stop one shout from firing five times.
- The visitor can refuse the microphone; the
  [permission entry](../../../help/errors/permission-denied-device.md)
  covers handling `"denied"` gracefully.

## Related components

- [AudioRecorder](audiorecorder.md): capturing the sound itself.
- [AudioLevel](../../data-types/audio-types.md): the value the
  form submits.

---
page_type: component
title: AudioRecorder
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - AudioRecorder
outcome: Record audio clips.
---

# AudioRecorder

Group: [Sound](../index.md#sound)

## Description

An `AudioRecorder` captures audio clips from the visitor's
microphone. It shows a record button; the visitor grants
permission, records until they stop (or a maximum length runs
out), and the finished clip is submitted with the form as a
[Recording](../../data-types/audio-types.md). Play clips back
with [Sound](sound.md).

## Syntax

```python
AudioRecorder(name)
AudioRecorder(name, max_duration=10000)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `max_duration` | `int` | `30000` | The longest allowed recording, in milliseconds. |
| `show` | `bool` | `True` | Display the recorder UI. |
| `on_record` | `str` | none | Route to call when a recording completes. |
| `on_denied` / `on_error` | `str` | none | Routes for refusal and failure. |

## Examples

A voice guestbook that keeps the latest message:

```python drafter height=360
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    last_message: str


@route
def index(state: State) -> Page:
    content = [
        Header("Voice Guestbook"),
        "Leave a message for the pets (10 seconds max):\n",
        AudioRecorder("message", max_duration=10000),
        "\n",
        Button("Leave message", "save")
    ]
    if state.last_message != "":
        content.append("\nThe latest message:\n")
        content.append(Sound(state.last_message))
    return Page(state, content)


@route
def save(state: State, message: Recording) -> Page:
    if message.data_url is None:
        return index(state)
    state.last_message = message.data_url
    return index(state)


start_server(State(""))
```

## Notes

- The route checks `data_url` for `None`, which covers refusal,
  errors, and submitting without recording, all at once.
- The completed `Recording` also carries `duration` (seconds)
  and `size` (bytes) for display.
- Clips stored in state survive page changes but, like all
  state, not a reload. [Download](../input/download.md)
  lets visitors keep one.
- Recording stops at `max_duration` automatically; a short limit
  keeps clips (and state) small.
- The `on_record` route can receive `duration` and `size` as
  parameters by name.

## Related components

- [Sound](sound.md): playback, with optional effects.
- [Microphone](microphone.md): measuring loudness without
  recording.
- [Recording](../../data-types/audio-types.md): the submitted
  value.

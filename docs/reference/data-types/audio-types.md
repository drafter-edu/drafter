---
page_type: reference
title: Audio types
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - AudioLevel
  - Recording
outcome: Use the microphone and recorder result types.
---

# Audio types

Two types carry sound out of the capture components.
`AudioLevel` is a snapshot of how loud things are, from
[Microphone](../components/sound/microphone.md). `Recording` is a
finished audio clip, from
[AudioRecorder](../components/sound/audiorecorder.md). Both
follow the same pattern as [Photo](photo.md) and the
[Location](location-types.md) type: a `status` field says whether
real data is present, and failures arrive as values instead of
exceptions.

## AudioLevel

A measurement of the microphone at the moment the form was
submitted.

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `status` | `str` | `"prompt"`, `"pending"`, `"granted"`, `"denied"`, `"error"`, or `"unavailable"`. |
| `message` | `str` or `None` | A description accompanying failures. |
| `volume` | `float` or `None` | Loudness right now, from 0.0 (silence) to 1.0 (as loud as the microphone measures). |
| `peak_volume` | `float` or `None` | The loudest moment since the page loaded. |
| `pitch` | `float` or `None` | The dominant frequency in Hz, when the sound is loud enough to estimate. |

```python
@route
def check(state: State, mic: AudioLevel) -> Page:
    if mic.volume is None:
        return Page(state, ["No microphone (" + mic.status + ")."])
    if mic.volume > 0.5:
        return Page(state, ["Too loud for the library!"])
    return Page(state, ["Nice and quiet."])
```

## Recording

A completed clip from an `AudioRecorder`.

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `status` | `str` | `"prompt"`, `"recording"`, `"granted"`, `"denied"`, `"error"`, or `"unavailable"`. |
| `message` | `str` or `None` | A description accompanying failures. |
| `data_url` | `str` or `None` | The recorded audio, or `None` when nothing has been recorded. |
| `duration` | `float` or `None` | Length in seconds. |
| `size` | `int` or `None` | Size in bytes. |

The `data_url` plays back directly: hand it to
[Sound](../components/sound/sound.md) (or
[Audio](../components/media/audio.md)) as its source. A recording
stored in state can therefore be replayed on any later page.

```python
@route
def playback(state: State, clip: Recording) -> Page:
    if clip.data_url is None:
        return Page(state, ["Nothing recorded (" + clip.status + ")."])
    state.last_clip = clip.data_url
    return Page(state, [
        "Here is your " + str(clip.duration) + " second clip:\n",
        Sound(state.last_clip)
    ])
```

## Notes

- Check the data field (`volume`, `data_url`) for `None` rather
  than memorizing status values; the check covers every failure
  at once.
- `volume` is a single number, not a stream: it describes the
  moment of submission. For reacting to sound as it happens, the
  `Microphone` component's `on_loud` and `on_quiet` events call
  routes for you.
- Recordings can be big. Storing many of them in state makes the
  app slow to snapshot; keep the latest one, or offer
  [Download](../components/input/download.md) instead of a
  collection.

## Related

- [Microphone](../components/sound/microphone.md) and
  [AudioRecorder](../components/sound/audiorecorder.md): the
  components that produce these values.
- [Sound](../components/sound/sound.md): playback.

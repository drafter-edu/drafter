---
page_type: playground
title: Camera, location, and sound
level: L4
audience: S
priority: P2
prereqs: []
symbols: []
outcome: Tinker with device features.
---

# Camera, location, and sound

Demos that reach for the device: camera, location, microphone,
and the speaker. The first three ask permission, and refusing is
part of the demo; watch how each app answers a "no". (The demos
run in a sandboxed frame, so your browser may ask an extra
time.)

## Strike a pose

Camera permission, then a photo, then every version of you.
Requires a webcam; try adding a `rotate(180)` print to the
gallery:

```python drafter height=480
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Passport Photos"),
        Camera("shot"),
        "\n",
        Button("Develop the roll", "develop")
    ])


@route
def develop(state: State, shot: Photo) -> Page:
    if shot.picture is None:
        return Page(state, [
            "No photo to develop (" + shot.status + ").\n",
            Button("Back to the studio", "index")
        ])
    return Page(state, [
        Header("The roll"),
        shot.picture.resize(120, 90),
        shot.picture.grayscale().resize(120, 90),
        shot.picture.flip_horizontal().resize(120, 90),
        "\n",
        Button("New pose", "index")
    ])


start_server(State())
```

## Where in the world

Location permission with a graceful no. Uses your real position;
nothing leaves the page:

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    report: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Am I Home Yet?"),
        CurrentLocation("where", show_coordinates=True),
        "\n",
        Button("Check", "check"),
        "\n" + state.report
    ])


@route
def check(state: State, where: Location) -> Page:
    if where.status != "granted":
        state.report = "No reading (" + where.status + "), " \
                       "so: possibly home, possibly not."
    else:
        state.report = ("You are at " + str(where.latitude)
                        + ", " + str(where.longitude)
                        + ", accurate to about "
                        + str(where.accuracy) + " meters.")
    return index(state)


start_server(State(""))
```

## Pin the map

No permission needed, but the map imagery does need the
internet. Click to leave a pin; try labeling pins with their
count:

```python drafter height=460
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pins: list[MapMarker]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Squirrel Sightings"),
        "Click where the squirrel was.\n",
        Map("spot", center=(39.68, -75.75), zoom=15,
            markers=state.pins, on_click="sighting")
    ])


@route
def sighting(state: State, latitude: float, longitude: float) -> Page:
    state.pins.append(MapMarker(latitude, longitude, "squirrel"))
    return index(state)


start_server(State([]))
```

## Shout meter

Microphone permission, then loudness as a game. Tune the
`threshold` down if your microphone is shy:

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    record_volume: float


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Wake the Dog"),
        "Babbage is asleep. Loudest attempt so far: "
        + str(round(state.record_volume, 2)) + "\n",
        Microphone("mic", threshold=0.4, cooldown=800,
                   on_loud="noise", visualize="bars"),
        "\n",
        Output("result", ["He sleeps on."])
    ])


@route
def noise(state: State, volume: float) -> Fragment:
    if volume > state.record_volume:
        state.record_volume = volume
        return Fragment(["A new record! He twitched an ear."],
                        target="#result")
    return Fragment(["Not your loudest. He sleeps on."],
                    target="#result")


start_server(State(0.0))
```

## Fanfare on demand

The speaker needs no permission, only a first click. Recompose
the victory tune, or slow the tempo to make it sad:

```python drafter height=260
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Sound Effects Shelf"),
        "Victory: ",
        Melody([("C4", 0.5), ("E4", 0.5), ("G4", 0.5), ("C5", 1.5)],
               tempo=160),
        "\nOminous: ",
        Melody([("E3", 2), ("D#3", 2)], tempo=60,
               waveform="sawtooth", effects=[Reverb(amount=0.7)]),
        "\nDoorbell: ",
        Tone("E5", duration=300)
    ])


start_server(State())
```

## Keep going

- [Camera](../../reference/components/capture/camera.md),
  [Map](../../reference/components/place/map.md),
  [CurrentLocation](../../reference/components/place/currentlocation.md),
  and [Microphone](../../reference/components/sound/microphone.md):
  every parameter, explained.
- [Device permission denied](../../help/errors/permission-denied-device.md):
  when the answer is no.

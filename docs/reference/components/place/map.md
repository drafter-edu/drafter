---
page_type: component
title: Map
level: L4
audience: S
priority: P1
prereqs: []
symbols:
  - Map
  - MapLocation
  - MapMarker
  - MapView
outcome: Show an interactive map with markers.
---

# Map

Group: [Place](../index.md#place)

## Description

A `Map` shows a real, interactive world map that visitors can pan,
zoom, and click. You can pin labeled markers on it, react to clicks
with a route, and read back the location a visitor chose. The map
imagery comes from OpenStreetMap, so it needs an internet
connection; without one, the map area shows a plain background but
still responds to clicks.

Three small data types come with it: `MapLocation` (a latitude and
longitude), `MapMarker` (a location plus a hover label), and
`MapView` (a center plus a zoom level, describing what the visitor
is looking at).

## Syntax

```python
Map(name)
Map(name, center=(latitude, longitude), zoom=13)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name. The most recently clicked spot is submitted under this name, like a form field. |
| `center` | pair of numbers, `MapLocation`, or `str` | `(0, 0)` | Where the map starts out centered, as `(latitude, longitude)`. |
| `zoom` | `int` | `13` | How close the map starts: about 2 shows the whole world, 13 a town, 18 a street. |
| `markers` | `list[MapMarker]` | none | Pins to display, each with an optional hover label. |
| `height` | `int` | `300` | Height of the map in pixels. |
| `persistent` | `bool` | `False` | Keep the live map (including where the visitor panned) across page re-renders. |
| `on_click` | `str` | none | Route to call when the map is clicked; it can receive `latitude` and `longitude`. |
| `on_marker_click` | `str` | none | Route to call when a marker is clicked; it can receive `latitude`, `longitude`, and `label`. |
| `on_move` | `str` | none | Route to call after panning or zooming; it can receive `latitude`, `longitude`, and `zoom`. |

## Examples

A map of good sniffing spots, with markers:

```python drafter height=440
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Ada's Favorite Parks"),
        Map("spot",
            center=(39.68, -75.75),
            zoom=14,
            markers=[
                MapMarker(39.681, -75.756, "The big field"),
                MapMarker(39.677, -75.749, "Squirrel tree"),
                MapMarker(39.686, -75.744, "Best puddle")
            ])
    ])


start_server(State())
```

Clicking the map calls a route, which adds a marker where the
click happened:

```python drafter height=480
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    sightings: list[MapMarker]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Domino Sighting Tracker"),
        "Click the map where you spotted the cat.\n",
        "Sightings: " + str(len(state.sightings)) + "\n",
        Map("spot",
            center=(39.68, -75.75),
            zoom=15,
            markers=state.sightings,
            on_click="record")
    ])


@route
def record(state: State, latitude: float, longitude: float) -> Page:
    state.sightings.append(MapMarker(latitude, longitude, "Domino!"))
    return index(state)


start_server(State([]))
```

## Notes

- Map imagery downloads from OpenStreetMap, so demos and deployed
  apps need an internet connection to show the actual map.
- The event routes take route names as strings, like a
  [Button](../actions/button.md), and receive the click's
  coordinates through parameters named `latitude` and `longitude`
  (plus `label` for marker clicks and `zoom` for view changes).
- The map also works as a form field: the last clicked spot is
  submitted under `name` when a Button submits the page, and a
  route parameter with that name annotated as `MapLocation`
  receives it. If the visitor never clicked the map, there is no
  location and the route stops with a friendly error, so prefer
  the `on_click` pattern unless a click is guaranteed.
- Latitude runs positive north and negative south; longitude runs
  positive east and negative west. `(39.68, -75.75)` is Newark,
  Delaware.
- Re-rendering the page rebuilds the map and snaps it back to your
  `center` and `zoom`; pass `persistent=True` to keep the
  visitor's current view instead, or handle `on_move` and store
  the view yourself.

## Related components

- [CurrentLocation](currentlocation.md): ask for the visitor's own
  location, which can then center a map.

## External links

- [Location data types](../../data-types/location-types.md)
- [Leaflet](https://leafletjs.com/), the mapping library
  underneath, and [OpenStreetMap](https://www.openstreetmap.org/),
  the source of the map imagery.

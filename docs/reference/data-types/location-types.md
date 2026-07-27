---
page_type: reference
title: Location and map types
level: L4
audience: S
priority: P2
prereqs: []
symbols:
  - Location
  - MapLocation
  - MapMarker
  - MapView
  - AddMarkerFunction
outcome: Use the geolocation and map value types.
---

# Location and map types

Five small types describe places. `Location` is what
[CurrentLocation](../components/place/currentlocation.md)
delivers: a position wrapped with permission information. The
`Map*` family belongs to [Map](../components/place/map.md):
plain positions, labeled pins, and the visitor's current view.
All latitudes and longitudes are decimal degrees, positive north
and east.

## Location

The result of asking for the visitor's position. Coordinates are
present only when `status` is `"granted"`.

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `status` | `str` | `"prompt"`, `"pending"`, `"granted"`, `"denied"`, `"error"`, or `"unavailable"`. |
| `message` | `str` or `None` | A description accompanying failures. |
| `latitude` | `float` or `None` | Degrees north (negative for south). |
| `longitude` | `float` or `None` | Degrees east (negative for west). |
| `accuracy` | `float` or `None` | How close the reading is, in meters. |
| `altitude` | `float` or `None` | Meters above sea level, when the device knows. |
| `heading` | `float` or `None` | Direction of travel in degrees, when moving. |
| `speed` | `float` or `None` | Meters per second, when moving. |
| `timestamp` | `float` or `None` | When the position was measured. |

Failures arrive as values (`status` plus `message`), never as
exceptions.

## MapLocation

A bare position: `MapLocation(latitude, longitude)`. Two uses:
as a map's `center` argument, and as the annotation for a route
parameter named after a `Map`, which then receives the last spot
the visitor clicked.

## MapMarker

A pin for a map's `markers` list:
`MapMarker(latitude, longitude, label)`. The label appears when
the visitor hovers over the pin and may be left out for an
unlabeled pin.

```python drafter height=400
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Where the pets sleep"),
        Map("spot",
            center=(39.68, -75.75),
            zoom=16,
            markers=[
                MapMarker(39.6805, -75.7515, "Ada's bed"),
                MapMarker(39.6801, -75.7508, "Captain's tower"),
                MapMarker(39.6798, -75.7512)
            ])
    ])


start_server(State())
```

## MapView

What the visitor is looking at after panning or zooming:
`latitude` and `longitude` of the center, plus `zoom` (about 2
for the whole world, 13 for a town, 18 for a street). A map's
`on_move` route receives these three as parameters; the dataclass
exists for storing a view in state so a later render can restore
it.

## AddMarkerFunction

Routes handling a map's click events can ask for a helper by
declaring a parameter `add_marker: AddMarkerFunction`. Calling
`add_marker("label")` pins the clicked spot on the live map
immediately, without re-rendering the page. The pin lives only on
the live map; record the location in state as well if the next
full render should still show it.

## Related

- [Map](../components/place/map.md) and
  [CurrentLocation](../components/place/currentlocation.md): the
  components these types serve.
- [Live updates](../../concepts/live-updates.md): how event
  routes receive values by parameter name.

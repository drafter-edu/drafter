---
page_type: component
title: CurrentLocation
level: L4
audience: S
priority: P1
prereqs: []
symbols:
  - CurrentLocation
  - Location
outcome: Ask for the user's location.
---

# CurrentLocation

Group: [Place](../index.md#place)

## Description

`CurrentLocation` asks the visitor to share where they are. It
shows a "Use my location" button; when the visitor agrees, the
browser asks for permission, and the resulting position is
submitted with the form under the component's name as a `Location`
value. The visitor can always say no, so your route must handle
both answers: a `Location` carries a `status` field telling you
whether coordinates are actually there.

## Syntax

```python
CurrentLocation(name)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `name` | `str` | required | The field's name, matching a parameter of the receiving route. |
| `show` | `bool` | `True` | Display the permission button and status text. |
| `show_coordinates` | `bool` | `False` | Also display the latitude and longitude once granted. |
| `enable_high_accuracy` | `bool` | `True` | Prefer the most precise position the device can give. |
| `timeout` | `int` | `10000` | How long to wait for a position, in milliseconds. |
| `maximum_age` | `int` | `0` | Accept a cached position up to this many milliseconds old. |
| `on_locate` | `str` | none | Route to call when a position (or a failure) is resolved. |
| `on_error` | `str` | none | Route to call when finding the location fails for any reason. |
| `on_denied` | `str` | none | Route to call when the visitor refuses permission. |
| `on_timeout` | `str` | none | Route to call when the request runs out of time. |

## Examples

The route checks `status` before using the coordinates, and the
component never raises an error, so no special error handling is
needed:

```python drafter height=340
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    report: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Lost Cat Reporter"),
        "Spotted Captain? Share where you are.\n",
        CurrentLocation("where", show_coordinates=True),
        "\n",
        Button("Report sighting", "report"),
        "\n" + state.report
    ])


@route
def report(state: State, where: Location) -> Page:
    if where.status == "granted":
        state.report = ("Sighting recorded at "
                        + str(where.latitude) + ", "
                        + str(where.longitude))
    else:
        state.report = "No location shared: " + where.status
    return index(state)


start_server(State(""))
```

## Notes

- The `status` field is one of `"prompt"` (not asked yet),
  `"pending"` (waiting), `"granted"`, `"denied"`, `"error"`, or
  `"unavailable"` (the device cannot report locations). Coordinates
  are only present when it is `"granted"`; otherwise `latitude` and
  `longitude` are `None` and `message` may explain why.
- A granted `Location` also carries `accuracy` (in meters) and,
  when the device knows them, `altitude`, `heading`, and `speed`.
- Browsers only allow location requests on secure pages. This is
  fine for deployed Drafter sites and local testing, but the
  request can fail as `"unavailable"` in unusual setups.
- Privacy matters here: ask for location only when your app
  genuinely uses it, show the visitor what you do with it (as the
  example does), and never display one visitor's location to
  others without clearly saying so.

## Related components

- [Map](map.md): show the reported position on a map.

## External links

- [Location data types](../../data-types/location-types.md)
- [The Geolocation API on MDN](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API)

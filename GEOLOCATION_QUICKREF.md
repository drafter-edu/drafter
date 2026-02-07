# CurrentLocation Component - Quick Reference

## Installation

Already integrated into Drafter v2. No additional installation needed.

## Basic Usage

```python
from drafter import *

@route
def index(state):
    return Page(state, [
        Header("Location Demo"),
        CurrentLocation("my_location"),
        Button("Submit", process_location)
    ])

@route
def process_location(state, my_location: Location):
    if my_location.status == "granted":
        return Page(state, [
            Header(f"Lat: {my_location.lat}, Lon: {my_location.lon}")
        ])
    return Page(state, [Header("Location not available")])

start_server()
```

## Component Options

```python
CurrentLocation(
    name,                    # Required: form field name
    show_coordinates=False,  # Optional: show lat/lon when granted
    **extra_settings         # Optional: HTML attributes (class, id, style, etc.)
)
```

## Location Dataclass

```python
@dataclass
class Location:
    status: str              # "unavailable" | "prompt" | "granted" | "denied" | "pending" | "error"
    message: Optional[str]   # Descriptive status message
    lat: Optional[float]     # Latitude in decimal degrees
    lon: Optional[float]     # Longitude in decimal degrees
    accuracy: Optional[float]  # Accuracy in meters
    altitude: Optional[float]  # Altitude in meters
    heading: Optional[float]   # Direction in degrees (0-360)
    speed: Optional[float]     # Speed in m/s
    timestamp: Optional[float] # Unix timestamp
```

## Status Values

- **`"unavailable"`**: Geolocation API not supported by browser
- **`"prompt"`**: Initial state, permission not yet requested
- **`"granted"`**: Permission granted, location available
- **`"denied"`**: User denied permission
- **`"pending"`**: Waiting for user to respond to permission prompt
- **`"error"`**: Error occurred (timeout, position unavailable, etc.)

## Example: Show Coordinates

```python
CurrentLocation("location", show_coordinates=True)
```

When permission is granted, displays:

```
✓ Location available
40.712800, -74.006000 (±10m)
```

## Example: Processing Different States

```python
@route
def handle_location(state, loc: Location):
    content = []

    if loc.status == "granted":
        content.append(Header("Location Received"))
        content.append(Paragraph(f"You are at ({loc.lat}, {loc.lon})"))
        if loc.accuracy:
            content.append(Paragraph(f"Accuracy: ±{loc.accuracy}m"))

    elif loc.status == "denied":
        content.append(Header("Location Blocked"))
        content.append(Paragraph("Please enable location access in your browser."))

    elif loc.status == "error":
        content.append(Header("Error"))
        content.append(Paragraph(loc.message or "Could not get location"))

    else:
        content.append(Header("Location Not Available"))

    content.append(Link("Back", index))
    return Page(state, content)
```

## Browser Compatibility

Works in all modern browsers that support:

- Geolocation API (navigator.geolocation)
- Optionally: Permissions API for checking existing permissions

Requires HTTPS in production (browsers restrict geolocation to secure contexts).

## Testing Locally

```powershell
# Run the example
uv run examples\geolocation_demo.py

# Open browser to http://localhost:8080
```

## Common Issues

### Location Not Working

- Ensure browser supports geolocation
- Check that user granted permission
- For production, must use HTTPS

### Permission Prompt Not Showing

- Browser might remember previous denial
- User needs to manually reset site permissions
- Some browsers block on localhost (use 127.0.0.1 instead)

## Implementation Details

See [GEOLOCATION_IMPLEMENTATION.md](GEOLOCATION_IMPLEMENTATION.md) for:

- Technical architecture
- Incomplete/missing features
- Known limitations
- Extension points

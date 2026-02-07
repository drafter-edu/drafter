"""Example demonstrating the CurrentLocation component for geolocation."""

from drafter import *


@route
def index(state):
    """Main page with geolocation component."""
    return Page(state, [
        Header("Geolocation Demo"),
        Paragraph("Click the button below to share your location:"),
        CurrentLocation("user_location", show_coordinates=True),
        Button("Submit Location", process_location),
    ])


@route
def process_location(state, user_location: Location):
    """Process the location data from the form."""
    content = [
        Header("Location Data Received"),
        Paragraph(f"Status: {user_location.status}"),
    ]
    
    if user_location.status == "granted":
        content.extend([
            Paragraph(f"Latitude: {user_location.lat}"),
            Paragraph(f"Longitude: {user_location.lon}"),
            Paragraph(f"Accuracy: ±{user_location.accuracy}m"),
        ])
        if user_location.altitude is not None:
            content.append(Paragraph(f"Altitude: {user_location.altitude}m"))
        if user_location.speed is not None:
            content.append(Paragraph(f"Speed: {user_location.speed}m/s"))
        if user_location.heading is not None:
            content.append(Paragraph(f"Heading: {user_location.heading}°"))
    elif user_location.status == "denied":
        content.append(Paragraph("Location access was denied. Please enable it in your browser settings."))
    elif user_location.status == "error":
        content.append(Paragraph(f"Error: {user_location.message}"))
    else:
        content.append(Paragraph("Location not available."))
    
    content.append(Link("Go Back", index))
    
    return Page(state, content)


start_server()

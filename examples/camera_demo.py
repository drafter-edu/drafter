"""Example demonstrating the Camera component for capturing photos."""

from drafter import *


@route
def index(state):
    """Main page with a camera component."""
    return Page(
        state,
        [
            Header("Camera Demo"),
            Paragraph("Enable your camera, then take a photo:"),
            Camera("snapshot", on_capture="/photo_taken"),
            Button("Submit Photo", process_photo),
            Paragraph(id="capture_output"),
        ],
    )


@route
def photo_taken(state, snapshot: Photo):
    """React as soon as a photo is captured, without leaving the page."""
    return Fragment(
        [
            Paragraph(f"Captured a {snapshot.width}x{snapshot.height} photo!"),
        ],
        target="#capture_output",
    )


@route
def process_photo(state, snapshot: Photo):
    """Process the photo data from the form."""
    content = [
        Header("Photo Received"),
        Paragraph(f"Status: {snapshot.status}"),
    ]

    if snapshot.status == "granted":
        content.extend(
            [
                Paragraph(f"Size: {snapshot.width}x{snapshot.height} pixels"),
                Image(snapshot),
            ]
        )
    elif snapshot.status == "denied":
        content.append(
            Paragraph(
                "Camera access was denied. Please enable it in your browser settings."
            )
        )
    elif snapshot.status == "error":
        content.append(Paragraph(f"Error: {snapshot.message}"))
    else:
        content.append(Paragraph("No photo was taken."))

    content.append(Link("Go Back", index))

    return Page(state, content)


start_server()

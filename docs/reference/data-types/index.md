---
page_type: index
title: Data types
level: L3
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Find value-type documentation.
---

# Data types

These pages document the value types Drafter defines for data that
Python has no built-in representation for: images, camera results,
locations, uploaded files, and sounds. All of them behave like
ordinary Python values: you can store them in state, pass them to
functions, and compare them in tests.

- [Picture](picture.md): an image as a Python value. The page covers
  constructors, transformations, pixel access, and conversions. This
  is the type you are most likely to need.
- [Photo](photo.md): the value a
  [Camera](../components/capture/camera.md) passes to your route,
  combining a picture with a status.
- [Location and map types](location-types.md): values that describe
  positions, used with [Map](../components/place/map.md) and
  [CurrentLocation](../components/place/currentlocation.md).
- [File types](file-types.md): values for uploaded files that keep
  their filename and metadata, used with
  [FileUpload](../components/input/fileupload.md).
- [Audio types](audio-types.md): values for sound levels and
  recordings, used with the
  [sound components](../components/index.md#sound).

All of these types follow the same pattern: a route *receives* a
value by annotating a parameter with the type, and a page *shows or
plays* a value through the matching component.

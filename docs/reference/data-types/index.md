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

Values Drafter defines for things Python has no built-in shape for:
images, camera results, locations, uploaded files, sounds. They all
behave like ordinary values: store them in state, pass them to
functions, compare them in tests.

- [Picture](picture.md): an image as a value; constructors,
  transformations, pixels, and conversions. The one you are most
  likely to want.
- [Photo](photo.md): what a [Camera](../components/capture/camera.md)
  hands your route: a picture plus a status.
- [Location and map types](location-types.md): where things are,
  for [Map](../components/place/map.md) and
  [CurrentLocation](../components/place/currentlocation.md).
- [File types](file-types.md): uploads that keep their filename and
  metadata, for [FileUpload](../components/input/fileupload.md).
- [Audio types](audio-types.md): sound levels and recordings, for
  the [sound components](../components/index.md#sound).

The pattern shared by all of them: a route *receives* one by
annotating a parameter with the type, and a page *shows or plays*
one through the matching component.

---
page_type: error
title: Camera, microphone, or location permission denied
level: L4
audience: S
priority: P2
prereqs: []
symbols: []
outcome: Handle denied device permissions.
error_text: "access denied"
---

# Camera, microphone, or location permission denied

## The error

```text
Camera access denied
Location access denied
```

Not a crash: the component shows a denied message where its
preview or button was, and the value your route receives has
`status` set to `"denied"`.

## What it means

The [Camera](../../reference/components/capture/camera.md),
[Microphone](../../reference/components/sound/microphone.md), and
[CurrentLocation](../../reference/components/place/currentlocation.md)
components all need the visitor's permission, granted through a
dialog the browser controls. "Denied" means the dialog was
refused, either right now or at some point in the past (browsers
remember the refusal for a site). Your program cannot override
it, and that is by design: the visitor owns the camera, not the
web page.

## Where to look

Nowhere in your code, at first. The state lives in the browser's
site permissions, usually behind the padlock or settings icon
next to the address bar.

## Check

- **Was the dialog refused by accident?** A stray click on
  "Block" is remembered.
- **Was it refused long ago?** A previous visit's refusal
  carries forward silently, so the dialog never even appears.
- **Is this an unusual context?** Embedded previews and insecure
  pages can be refused by policy; the docs' own embedded demos
  ask for permission inside the sandboxed frame, and a refusal
  there behaves the same way.

## Fix

For yourself while developing: open the browser's site
permissions (padlock icon), set the camera, microphone, or
location back to "Ask" or "Allow", and reload.

For your visitors, in code: treat `"denied"` as a normal answer.
Check the status (or the data field for `None`) and respond with
a page that explains what the feature would have done and how to
proceed without it:

```python
@route
def report(state: State, where: Location) -> Page:
    if where.latitude is None:
        return Page(state, [
            "No location was shared, so pick your spot "
            "on the map instead.\n",
            Button("Choose on a map", "map_page")
        ])
    return save_spot(state, where)
```

## Confirm

Developing: after resetting the permission, the component shows
its prompt again and the dialog reappears on request. In code:
deny the permission yourself and check that your app shows the
graceful page instead of a confusing blank.

## Prevent

Ask only when the feature needs it, on the page where the visitor
can see why. A camera request on the "take your pet's portrait"
page gets granted; the same request on the front page gets
refused. And test the denied path once before deploying, because
some of your visitors will refuse on principle.

## Understand

The permission-based components share this design: refusals
arrive as `status` values, never as exceptions. The
[Photo](../../reference/data-types/photo.md),
[Location](../../reference/data-types/location-types.md), and
[audio](../../reference/data-types/audio-types.md) type pages
list every status each can report.

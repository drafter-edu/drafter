---
page_type: error
title: Link or button points to an unknown route
level: L2
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Fix a link or button that points to an unknown route.
error_text: "points to non-existent page"
error_id: payload.verification_failed
---

# Link or button points to an unknown route

## The error

The error page has this title:

```text
Unusable Value
```

Drafter uses the title "Unusable Value" for several different
problems, so the sentence under the title is what identifies this
one:

```text
The link labeled 'Next' tries to go to a page named `sumary`, but your
site has no route with that name.
```

The technical message below it reads:

```text
payload.verification_failed: Payload verification failed for the page 'index':
While verifying the Page() object returned from index, an error was encountered:
Link `Next` points to non-existent page `sumary`.
```

Both messages say "link" even when the component is a `Button`.
Drafter checks buttons and links the same way, so
`Button("Next", "sumary")` and `Link("Next", "sumary")` produce the
same text.

A different error page, titled "Page Not Found", appears when the
address in the browser names a route your program does not have, for
example an address that ends in `?route=sumary`:

```text
Drafter could not find the page route your app tried to open.
request.route_not_found: No route found for URL: sumary
```

That page can appear after you rename or delete a route and then
reload a browser tab that was showing it. Its "Return to Index Page"
link takes you back to a page that exists.

## What it means

Before showing a page, Drafter checks that every button and link on
it points at a real route. One of yours names a route that does not
exist, so Drafter stopped the page rather than render it with a
button or link that leads nowhere.

## Where to look

The first message names the label and the target. The technical
message also names the route whose page holds the button or link
("returned from index"). Search that route for the `Button(...)` or
`Link(...)` call with that label, then compare its target string
against the names of your route functions.

## Check

Three causes produce this error. The message is the same for all
three, so check your code for each one:

- **A typo**: the target almost matches a route name (`"sumary"` vs
  `def summary`). Capital letters count, so `"Summary"` does not
  match `def summary`.
- **A missing decorator**: the function exists, but has no `@route`
  above it, so Drafter never registered it as a route.
- **A route you have not written yet**: you wired the button before
  writing its destination.

## Fix

Make the target string match a decorated route exactly:

```python
@route
def summary(state: State) -> Page:
    ...

# In the page that links there:
Button("Next", "summary")
```

The third hint under "What To Try Next" on the error page suggests
passing the route function itself, as in `Button("Next", summary)`
with no quotation marks. Both forms work and lead to the same route,
and when you use a string, as these docs do, the string must match
the name of the function exactly.

## Confirm

Reload and click the fixed control; the target page should render.
If you have tests, add
`assert_has(index(state), Button("Next", "summary"))` so the
connection stays checked.

## Prevent

Name routes with plain, short, lowercase names you can spell
confidently, and write the destination route (even as a stub
returning a bare page) before wiring buttons to it.

## Understand

[Routes and pages](../../concepts/routes-and-pages.md) explains how
route names become addresses and how Drafter verifies connections;
[Add and connect pages](../../add/pages.md) is the how-to.

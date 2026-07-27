---
page_type: misconception
title: Student misconceptions
audience: T
priority: P1
prereqs: []
symbols: []
outcome: Anticipate and repair student misconceptions.
search:
  exclude: true
---

# Student misconceptions

Each entry states the belief the way a student would, explains why a
reasonable person forms it, and suggests a repair move that might help.
The list is a floor, not a ceiling; when you find a new
one, it belongs here.

## "Everyone who visits my site sees my state"

**Why it's plausible.** Real websites work this way: when you post
something, other people see it. Students have a decade of
experience with shared server state.

**What's actually true.** Each visitor's browser runs its own
private copy of the program. State lives in that tab's memory,
is not shared with anyone, and vanishes on reload.

**How it shows up.** Project proposals with chat rooms,
leaderboards, or "other players"; the question "how do I see what
my friend entered?"; surprise that reloading resets everything.

**How to repair.** Open the deployed app in two browser windows
side by side and change state in one. The other never changes.
Then name the rule: every visitor gets a fresh, private copy.

**Related docs.** [How Drafter works](../start/how-drafter-works.md),
[State](../concepts/state.md).

## "My program runs top to bottom, like my other programs"

**Why it's plausible.** Every program the course has shown them
did exactly that.

**What's actually true.** The top-level code runs once, at
startup. After that the app is event-driven: nothing happens
until a click or a form submission calls a route, and routes run
in whatever order the visitor causes.

**How it shows up.** Code placed after `start_server(...)` that
"never runs"; routes written to depend on another route having
run first; confusion about why `index` runs again later.

**How to repair.** Trace one click in the debugger's History tab:
which route ran, with what state, returning what page. The
program is a collection of functions waiting to be called, and
the visitor decides the order.

**Related docs.** [Routes and pages](../concepts/routes-and-pages.md),
[Troubleshooting](../help/troubleshooting.md).

## "My app is running on a server somewhere"

**Why it's plausible.** "Website" implies "server" in every other
context students know, and the deploy step even puts the app at a
real URL.

**What's actually true.** Deployment copies static files to
GitHub Pages. The Python runs inside each visitor's browser;
there is no machine of yours executing anything.

**How it shows up.** Expecting uploaded data to "be on the site"
for others; asking where the database is; worrying the app stops
working when their own computer is off (or not realizing the
localhost URL does die with their program).

**How to repair.** Show the compiled output folder: the app is
files, like a PDF, and the browser is the machine that runs them.

**Related docs.** [How the web works](../concepts/how-the-web-works.md),
[Deploy and submit](../your-project/deploy/index.md).

## "My login page keeps my data safe"

**Why it's plausible.** It looks exactly like real login pages,
and it does control which page the visitor sees next.

**What's actually true.** The entire program, passwords included,
ships to every visitor's browser, where the source is one
right-click away. A Drafter login is a flow simulation, not a
security boundary.

**How it shows up.** Projects storing a "secret" password in
code; students asking how to keep other students out of the
admin page; grading rubrics that accidentally reward "security"
features.

**How to repair.** Open the browser's view-source on the deployed
app and find the password together. Then draw the line: login
pages are fine as user-experience practice, as long as nobody
calls them protection.

**Related docs.** [Security honestly](../extend/security.md),
[Login flow example](../examples/login.md).

## "The back button undoes my last action"

**Why it's plausible.** In documents and most websites, back
means "return to how things were".

**What's actually true.** The back button replays the route that
built the previous page, with the state as it is now. It re-runs
a function; it does not restore old state.

**How it shows up.** "The counter did not go back down"; games
where players discover back-button behavior as an exploit or a
bug; tests that pass while manual back-button poking confuses.

**How to repair.** A counter app: click increment three
times, press back, watch the count stay at three. Then trace it
in the History tab, which shows the route re-running.

**Related docs.** [State](../concepts/state.md),
[See inside your app](../start/debug-panel.md).

## "My test has to match the whole page exactly"

**Why it's plausible.** The first test students see compares a
whole result (`assert_state` with a full `State`), and frozen
regression tests really do snapshot whole pages.

**What's actually true.** The everyday assertions are loose:
`assert_has(page, "Score: 3")` checks that one thing is present
and ignores the rest. Whole-page freezing is a separate tool for
finished pages.

**How it shows up.** Enormous brittle assertions copied from page
output; tests abandoned after the first styling change breaks
them all; "testing is annoying" sentiment.

**How to repair.** Live-refactor one brittle test into two
`assert_has` checks, then restyle the page and re-run: the loose
tests survive.

**Related docs.** [Test a feature](../add/test-a-feature.md),
[Freeze finished pages](../add/freeze-pages.md).

## "Styling changed how my program behaves"

**Why it's plausible.** The page looks different, and to a novice
"looks different" and "is different" are the same observation.

**What's actually true.** Styling functions and `style_` keywords
change presentation only. State, routes, and tests see the same
values; a styled component still submits the same form data.

**How it shows up.** Re-running every test after a color change
"to be safe"; conversely, blaming a logic bug on a styling edit
made at the same time; asking whether `float_right` moves data.

**How to repair.** Style a component in the middle of class and
re-run the tests untouched, then break a route and show which
failure actually looks like a logic failure.

**Related docs.** [Change the appearance](../add/change-appearance/index.md),
[Styling functions](../reference/styling-functions.md).

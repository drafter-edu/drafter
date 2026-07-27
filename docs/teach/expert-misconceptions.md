---
page_type: misconception
title: Expert misconceptions
audience: T
priority: P1
prereqs: []
symbols: []
outcome: Correct experienced-developer assumptions about Drafter.
search:
  exclude: true
---

# Expert misconceptions

Experienced web developers and instructors mispredict Drafter more
confidently than novices do, because Drafter looks like things
they already know. Each entry below states the assumption, honors
the analogy that produced it, and marks exactly where the analogy
breaks.

## "It's basically Flask for kids"

**Why it's plausible.** The `@route` decorator, functions mapped
to URLs, and a `start_server` call are straight out of the Flask
playbook, deliberately.

**What's actually true.** There is no backend. The decorators
build the same mental shapes as Flask, but the program is
compiled into the page and executes in each visitor's browser via
Pyodide. No requests cross a network, no process serves anyone,
and two visitors never share anything.

**How it shows up.** Planning lessons around request/response
vocabulary; expecting `request` objects, sessions, or middleware;
assuming students can add a database "later" within Drafter.

**How to repair.** Read
[How Drafter works](../start/how-drafter-works.md), which is
short and student-facing; the analogy holds for code shape and
breaks for architecture.

**Related docs.** [Why Drafter](why-drafter.md),
[Moving on to Flask](../extend/flask.md).

## "State is a session"

**Why it's plausible.** A per-visitor bundle of values that
routes read and write is exactly what a session is for.

**What's actually true.** State is an in-memory Python object in
one browser tab. Nothing is stored server-side (there is no
server side), nothing is shared between tabs, and a reload
constructs a fresh `State` from your defaults.

**How it shows up.** Assignments that assume data survives
between visits; surprise that "logging in" does not persist;
looking for the session store configuration.

**How to repair.** Reload a running app and watch the state
reset; there is nowhere else the data could have been.

**Related docs.** [State](../concepts/state.md),
[Student misconceptions](student-misconceptions.md) (students
form the same belief from the other direction).

## "Deploying this needs a server, so deployment must be the hard week"

**Why it's plausible.** Deploying student Flask apps genuinely is
painful: hosting, WSGI, environment variables, databases.

**What's actually true.** `drafter file.py --compile` produces
static files, and GitHub Pages serves them free. The deployment
guide is a student-followable checklist, and the usual failure
modes are a syntax error or a misnamed file, not infrastructure.

**How it shows up.** Cutting deployment from the syllabus to
save time, which discards the most motivating week Drafter
offers.

**How to repair.** Walk the published guide once yourself; it is
a half-hour end to end.

**Related docs.** [Deploy and submit](../your-project/deploy/index.md).

## "The source is compiled away, so code is reasonably private"

**Why it's plausible.** "Compile" suggests the Python becomes
something unreadable, the way native compilation does.

**What's actually true.** Compiling bundles the source into the
page; the browser needs it to run the app. Anyone can read any
deployed Drafter app's full source, and students should be told
so before they embed anything sensitive (API keys, answer keys,
grading logic).

**How it shows up.** Course designs where the deployed app
contains quiz answers; instructors embedding a private API key in
a demo.

**How to repair.** View source on any deployed Drafter app and
find the Python in it.

**Related docs.** [Security honestly](../extend/security.md).

## "It renders server-side, so the browser only gets HTML"

**Why it's plausible.** Returning a page-describing object from a
route function is the shape of server-side rendering.

**What's actually true.** Rendering happens in the browser too.
The Python builds component trees; a JavaScript layer turns them
into DOM in the visitor's tab. Consequences: the first load pays
a Pyodide boot cost measured in seconds, and everything after
that is local and fast.

**How it shows up.** Judging Drafter as "slow" from the first
load; expecting server logs; puzzling over how a "server-rendered"
app works from a static host.

**How to repair.** Open a deployed app with the network tab open:
after the initial load, no requests carry app logic.

**Related docs.** [Python in the browser](../extend/pyodide.md).

## "Dataclass state means dictionaries aren't supported"

**Why it's plausible.** Every example in the documentation uses
dataclasses and lists, without exception.

**What's actually true.** Dictionaries, sets, and most built-in
types store fine in state. The docs avoid them because the target
audience has not learned them yet; it is an audience decision,
not a technical limit.

**How it shows up.** Telling students Drafter "can't do dicts";
contorted dataclass designs in instructor-written starter code
where a dict was the right call for your course's level.

**Related docs.** [Beyond the student docs](beyond-the-basics.md),
[State](../concepts/state.md).

---
page_type: how-to
title: What Drafter can do
level: L2
audience: S
priority: P1
prereqs: [your-project]
symbols: []
outcome: Discover features you have not met yet and find a project idea that excites you.
---

# What Drafter can do

## Goal

You are about to pick a final project, and you want it to be interesting.
This page is a tour of the parts of Drafter that
the guided projects did not show you: sound, cameras, maps, timers,
charts, live typing, files, and more. Each part is short. Read the
ones that sound fun, follow the links to try the live demos, and
collect ideas as you go.

You do not need to understand every line of code here. The point is
to know what is possible, so that when you plan your project you can
say "Drafter can do that" and go find out how.

## Before you start

Everything on this page uses the same three ideas you already know:

- A **route** is a function that returns a `Page`.
- **State** is a dataclass that remembers things between clicks.
- A **component** is a Python object, like `Button` or `TextBox`,
  that becomes part of a page.

The new components below work the same way. Most of them simply
hand your route a new kind of value: a photo, a location, a sound
clip, or the number of seconds that passed. Your route decides what
to do with it.

Every feature here has a full reference page with every parameter
and a working demo. When a feature catches your eye, open its link.
If you are using an AI assistant to help you program, paste that
link into the chat so the assistant works from the real
documentation. There is more advice about that near the end of this
page.

## Make sound without any sound files

Drafter can play notes straight from Python. No audio files are
needed. `Tone` plays one note, and `Melody` plays a list of notes
with a tempo. Both can use different waveforms, like a buzzy
`"square"` or a bright `"sawtooth"`, and both accept effects like
`Echo` and `Reverb`.

```python drafter height=220
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Victory Fanfare"),
        Melody([("C4", 0.5), ("E4", 0.5), ("G4", 0.5), ("C5", 1.5)],
               tempo=160),
        "\nWith echo: ",
        Melody([("C4", 0.5), ("E4", 0.5), ("G4", 0.5), ("C5", 1.5)],
               tempo=160, effects=[Echo()]),
        "\nDoorbell: ",
        Tone("E5", duration=300)
    ])


start_server()
```

A melody is a plain Python list, so a loop can build one. That means
your program can **compose music** from data: a song from the
letters of a name, a tune that gets faster as the game gets harder,
or a random melody generator.

**Project sparks**: a tiny piano, a song-guessing game, a
"name to melody" converter, a Morse code trainer, a sound effects
board for a story.

**Look it up**: [Tone](../reference/components/sound/tone.md),
[Melody](../reference/components/sound/melody.md),
[Audio effects](../reference/components/sound/effects.md),
[Sound](../reference/components/sound/sound.md) for playing files
with effects, and [Audio](../reference/components/media/audio.md)
for background music that keeps playing across pages.

## Record the visitor's voice

`AudioRecorder` shows a record button. The visitor records a short
clip, and your route receives it as a `Recording`. You can play it
back with `Sound`, and `Sound` can change the speed, add an echo, or
muffle it like a voice through a wall.

```python
AudioRecorder("shout", max_duration=5000)
```

```python
@route
def cave(state: State, shout: Recording) -> Page:
    if shout.data_url is None:
        return index(state)
    return Page(state, [
        "Chipmunk version: ", Sound(shout.data_url, speed=1.6),
        "\nCavern version: ", Sound(shout.data_url, effects=[Reverb()])
    ])
```

The visitor can always refuse the microphone. When that happens the
recording arrives empty, and your code checks for `None` instead of
crashing.

**Project sparks**: a voice memo board, a "say the password" game, a
pronunciation practice app, a sound-effect transformer.

**Look it up**:
[AudioRecorder](../reference/components/sound/audiorecorder.md) and
[Audio types](../reference/data-types/audio-types.md).

## Use the camera and edit photos

`Camera` asks permission, shows a live preview, and sends the photo
to your route. The photo arrives as a `Picture`, which is a Python
value you can store in state, transform, and compare in tests.

Pictures come with transformations. Each one returns a new picture,
so you can show the original and every version side by side.

```python
@route
def develop(state: State, shot: Photo) -> Page:
    if shot.picture is None:
        return Page(state, ["No photo (" + shot.status + ")."])
    return Page(state, [
        shot.picture.resize(120, 90),
        shot.picture.grayscale(),
        shot.picture.flip_horizontal(),
        shot.picture.rotate(90),
        Download("Save it", "photo.png", shot.picture)
    ])
```

You can also work pixel by pixel. `get_pixel(x, y)` returns a color
and `set_pixel(x, y, color)` changes one, so a loop can invert
colors, draw a border, or hide a secret message in an image.
`Picture.new(width, height, color)` creates a blank picture from
nothing, which means your program can draw its own art.

Visitors can upload existing pictures with `FileUpload`, and
`Download` lets them keep the result.

**Project sparks**: a photo booth with filters, a pixel-art editor,
a "spot the difference" generator, a profile picture maker, a
meme captioner.

**Look it up**: [Camera](../reference/components/capture/camera.md),
[Picture](../reference/data-types/picture.md),
[Use pictures](../add/pictures.md), and the
[photo editor example](../examples/photo-editor.md).

## Put things on a real map

`Map` shows a real, scrollable world map. You can pin markers with
labels, and a click on the map calls one of your routes with the
latitude and longitude of the spot.

```python
Map("spot", center=(39.68, -75.75), zoom=15,
    markers=state.pins, on_click="add_pin")
```

```python
@route
def add_pin(state: State, latitude: float, longitude: float) -> Page:
    state.pins.append(MapMarker(latitude, longitude, "Seen here"))
    return index(state)
```

`CurrentLocation` asks the visitor for their real position. If they
say yes, your route receives the coordinates. If they say no, the
value's `status` tells you, and the app keeps working.

The map pictures come from the internet, so the map needs a
connection. Clicks still work without one.

**Project sparks**: a campus food map, a travel wish list, a
"guess the city" game, a lost-and-found board, a running route
logger, a scavenger hunt that checks how close you are.

**Look it up**: [Map](../reference/components/place/map.md),
[CurrentLocation](../reference/components/place/currentlocation.md),
and [Location and map types](../reference/data-types/location-types.md).

## React while the visitor types

So far your apps change only when a button is clicked. Any
component can also fire an event, like `on_input` for every
keystroke or `on_change` when a choice settles. The route that
answers can return a `Fragment`, which replaces one small part of
the page instead of the whole thing.

```python drafter height=240
from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Password Strength"),
        TextBox("password", "", on_input="judge"),
        "\n",
        Output("verdict", ["Type a password."])
    ])


@route
def judge(password: str) -> Fragment:
    if len(password) < 6:
        verdict = "Too short."
    elif password.lower() == password:
        verdict = "Add a capital letter."
    else:
        verdict = "Strong enough for a cat."
    return Fragment([verdict], target="#verdict")


start_server()
```

A route can also return `Update`, which changes state silently with
no visible reaction. That is how autosave works: every keystroke is
saved, and the visitor can wander off to another page and come back
to their draft.

**Project sparks**: a live word counter, a rhyme suggester, a unit
converter that updates as you type, a search box that filters a
list, a typing speed test.

**Look it up**: [Add live behavior](../add/live-behavior.md),
[Fragment](../reference/fragment.md),
[Update](../reference/update.md), and
[Keyword attributes](../reference/keyword-attributes.md) for the
full list of events.

## Make things happen over time

`Timer` counts down and calls a route when it reaches zero. `Clock`
ticks forever and calls a route on every tick. Both measure in
milliseconds, so one second is `1000`.

```python drafter height=240
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    hunger: int


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Tamagotchi Minute"),
        Clock(2000, "hungrier", show=False),
        Output("status", ["Captain is content."]),
        "\n",
        Button("Feed", "feed")
    ])


@route
def hungrier(state: State) -> Fragment:
    state.hunger = state.hunger + 1
    if state.hunger < 3:
        mood = "Captain is content."
    else:
        mood = "Captain demands salmon. (" + str(state.hunger) + ")"
    return Fragment([mood], target="#status")


@route
def feed(state: State) -> Page:
    state.hunger = 0
    return index(state)


start_server(State(0))
```

Normally a timer is part of the page that made it, so leaving the
page stops it. Add `persistent=True` and the countdown keeps running
while the visitor checks their inventory on another page.

**Project sparks**: a speed quiz, an idle clicker game, a pomodoro
study timer, a slideshow that advances itself, a reaction-time test,
a pet that gets hungry while you are away.

**Look it up**: [Make things happen over time](../add/timers.md),
[Timer](../reference/components/time/timer.md), and
[Clock](../reference/components/time/clock.md).

## Listen to the room

`Microphone` does not record anything. It measures how loud the room
is and calls a route when the sound crosses a threshold. It can also
draw a live volume meter, waveform, or bars.

```python
Microphone("mic", threshold=0.4, on_loud="noise", visualize="bars")
```

```python
@route
def noise(state: State, volume: float) -> Fragment:
    if volume > state.record:
        state.record = volume
    return Fragment(["Loudest so far: " + str(round(state.record, 2))],
                    target="#result")
```

**Project sparks**: a clap-to-start game, a "shout meter" contest,
a classroom noise warning, a game where silence ends your turn.

**Look it up**:
[Microphone](../reference/components/sound/microphone.md).

## Draw charts and pictures from data

Drafter apps run real Python, so the plotting library matplotlib
works. Draw a chart in your route, add `MatPlotLibPlot()` to the
page, and the chart redraws from state on every visit.

```python
import matplotlib.pyplot as plt

@route
def index(state: State) -> Page:
    plt.bar(range(len(state.walks)), state.walks)
    plt.title("Blocks walked with Babbage")
    return Page(state, [
        Header("Walk Tracker"),
        MatPlotLibPlot(),
        Button("Log a long walk", "long_walk")
    ])
```

For shapes, `SVG` takes drawing instructions as text. A loop can
build a row of circles, a bar chart with your own colors, or a
simple game board. For pixel art, `Picture.new` and `set_pixel` work
too.

**Project sparks**: a mood tracker with a weekly chart, a budget
app with a spending graph, a dice-roll probability demo, a
generative art page where every visit draws something new.

**Look it up**:
[MatPlotLibPlot](../reference/components/media/matplotlibplot.md),
[SVG](../reference/components/media/svg.md), and the
[images playground](../examples/playground/media.md).

## Move files in and out

Your app runs inside the browser tab, so it cannot read the
visitor's hard drive on its own. Two components move files across
that boundary. `FileUpload` lets the visitor choose a file, and your
route's type annotation decides what arrives: `str` for text,
`bytes` for anything, or `Picture` for an image. `Download` offers a
file your app built, such as a text log or a CSV that opens in a
spreadsheet.

```python
FileUpload("poem_file", accept=".txt")
Download("Download the journal", "journal.txt", journal_text)
```

Your app can also read data files that you ship with it, using
plain `open()`. That is how you give a quiz app two hundred
questions without typing them into Python.

**Project sparks**: a word-frequency analyzer, a grade book that
imports a CSV, a flashcard app that reads decks from text files, a
journal with a "download my entries" button.

**Look it up**: [Upload and download files](../add/files.md) and
[File types](../reference/data-types/file-types.md).

## Collect dates, show progress, hide details

Some small components make apps feel finished with very little
code.

- `DateInput`, `TimeInput`, and `DateTimeInput` show the browser's
  own calendar picker. Annotate the route parameter as `date` and
  you receive a real Python date with `.year` and `.month`.
- `ProgressBar(answered, total)` draws a bar that fills up.
- `Meter(value, min=0, max=100, low=30, high=70, optimum=10)` draws a
  gauge that changes color when the value leaves the healthy zone.
- `Details("Hint", "The answer is...")` is a collapsible section.
  Give several the same `group` and they become an accordion where
  opening one closes the others.
- `Table(state.entries)` turns a list of dataclasses into a table in
  one line.

**Project sparks**: a countdown to an event, a habit tracker with
streak gauges, a study guide with hidden answers, a pet health
dashboard.

**Look it up**: [DateInput](../reference/components/input/dateinput.md),
[ProgressBar](../reference/components/data/progressbar.md),
[Meter](../reference/components/data/meter.md),
[Details](../reference/components/layout/details.md), and
[Table](../reference/components/data/table.md).

## Change the whole look in one line

There are more than twenty themes. One call at the top of your
program restyles every page:

```python
set_website_style("terminal")
```

A few more one-liners: `set_website_title("Snack Tracker")` names
the browser tab, `set_website_favicon("icon.png")` gives it an icon,
and `set_page_transition("fade")` makes pages fade in. Every
component also accepts `style_` keywords, like
`Button("Go", "start", style_font_size="24px")`, and you can add
your own CSS for anything else.

**Look it up**: the [theme catalog](../reference/themes.md),
[Change the appearance](../add/change-appearance/index.md), and
[Site configuration](../reference/site-config.md).

## Use other Python libraries

Because your app is real Python, `import random` works, and so do
many libraries from PyPI. When Drafter sees an import in your file,
it installs that library in the browser before your app runs. You
also need the library installed on your own computer, with pip or
your editor's package manager, so the first local run works.

Not every library can run in a browser. The scientific libraries
have special browser builds, and any pure-Python package installs
fine. Libraries that need a database, other processes, or network
sockets cannot work, and no setting changes that. The quick test is
to search
[Pyodide's package list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html).

Here are ten libraries that work in Drafter and that engineers tend
to find useful. Each link goes to a beginner tutorial.

1. **[NumPy](https://numpy.org/doc/stable/user/absolute_beginners.html)**
   is the foundation of scientific Python. It gives you arrays, so
   you can add two lists of a thousand measurements in one line,
   take averages, and do matrix math. Most of the other libraries
   here are built on it. Spark: a signal viewer that averages noisy
   sensor readings.
2. **[pandas](https://pandas.pydata.org/docs/user_guide/10min.html)**
   reads a CSV file into a table and lets you sort, filter, group,
   and summarize it. Pair it with `FileUpload` and your app becomes
   a data explorer for any spreadsheet. Spark: a lap-time analyzer
   that reads a race log and reports the fastest lap per driver.
3. **[Matplotlib](https://matplotlib.org/stable/users/explain/quick_start.html)**
   draws line charts, bar charts, scatter plots, and histograms.
   `MatPlotLibPlot()` puts the result on a page. Spark: a stress
   versus strain plot built from values the visitor types in.
4. **[SciPy](https://docs.scipy.org/doc/scipy/tutorial/index.html)**
   adds the heavy numerical tools: solving equations, finding
   minimums, integrating, fitting curves to data, and filtering
   signals. Spark: a curve-fitting tool that finds the best line or
   exponential through uploaded data points.
5. **[SymPy](https://docs.sympy.org/latest/tutorials/intro-tutorial/index.html)**
   does algebra with symbols instead of numbers. It can simplify
   expressions, solve for `x`, take derivatives and integrals, and
   print the result as nice math. Spark: a step-by-step calculus
   helper that shows the derivative of whatever the visitor enters.
6. **[Pint](https://pint.readthedocs.io/en/stable/getting/tutorial.html)**
   handles physical units. Multiply `3 * ureg.meter` by
   `2 * ureg.second` and the result knows it is in meter-seconds, and
   converting to feet or miles per hour is one method call. Pint is
   pure Python, so it installs from PyPI the first time your app
   imports it. Spark: a unit converter that refuses to add meters to
   seconds and explains why.
7. **[NetworkX](https://networkx.org/documentation/stable/tutorial.html)**
   builds graphs: nodes connected by edges. It can find the shortest
   path, detect cycles, and measure which node is most central.
   Spark: a campus map that finds the shortest walk between two
   buildings, or a circuit checker that finds loops.
8. **[Shapely](https://shapely.readthedocs.io/en/stable/manual.html)**
   works with 2D geometry: points, lines, and polygons. It can
   compute areas, test whether a point is inside a shape, and find
   where two shapes overlap. Spark: a floor-plan tool that checks
   whether furniture fits in a room, or a zone checker for `Map`
   clicks.
9. **[Pillow](https://pillow.readthedocs.io/en/stable/handbook/tutorial.html)**
   is the standard image library. It can blur, sharpen, draw text
   and shapes, and adjust brightness. Drafter's `Picture` converts to
   and from a Pillow image with `Picture.from_pil`, so you can use
   Pillow for the steps `Picture` does not cover. Spark: a photo
   booth that stamps a caption and a date onto each camera shot.
10. **[scikit-learn](https://scikit-learn.org/stable/getting_started.html)**
    is the beginner-friendly machine learning library. Give it a
    table of examples and it can learn to predict a number or sort
    items into categories. Spark: a predictor that estimates a
    bridge's load limit from a few measurements, trained on a small
    dataset you bundle with the app.

The standard library counts too. `random`, `statistics`, `math`,
`fractions`, and `datetime` all work with no installation.

`requests` can fetch data from public web APIs, with one catch: the
other website has to allow browser requests. Public data services
often do. Ordinary websites usually do not, and nothing in your code
can change that. These five need no account or key, allow browser
requests, and return JSON that `requests.get(url).json()` turns into
Python values:

1. **[Open-Meteo](https://open-meteo.com/en/docs)** gives the
   current weather and a seven-day forecast for any latitude and
   longitude, plus air quality, wind, and solar radiation. Spark: a
   "should I bike today?" page, or a solar-panel output estimator.
2. **[USGS Earthquake feed](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)**
   lists every earthquake recorded in the last hour, day, or week,
   with magnitude and location. Spark: drop each quake on a `Map`
   as a marker sized by magnitude.
3. **[Where the ISS at](https://wheretheiss.at/w/developer)**
   reports the International Space Station's position, altitude,
   and speed right now. Spark: a `Clock` that re-fetches every few
   seconds and moves a marker across a `Map`.
4. **[Frankfurter](https://frankfurter.dev/)** publishes daily
   currency exchange rates from the European Central Bank. Spark: a
   parts-cost calculator that converts supplier prices into dollars.
5. **[Sunrise-Sunset](https://sunrise-sunset.org/api)** returns
   sunrise, sunset, and day length for a location and date. Spark:
   combine it with `CurrentLocation` to show how much daylight is
   left where the visitor is standing.

The answers come back as dictionaries, which your course may not
have covered yet. Ask your instructor or your AI assistant to show
you how to pull one value out, and look at the raw answer in the
browser first so you know what you are looking for.

Heavy libraries make the first page load slower, because the browser
has to download them once. Matplotlib is several megabytes, and
scikit-learn and SciPy are larger. Warn your visitors on the first
page, and only import what you use.

**Project sparks**: a dice game with real randomness, a data
explorer for a public dataset you bundle with the app, a weather
page for your town, a unit-aware engineering calculator.

**Look it up**: [Third-party libraries](../extend/packages.md).

## Reach the browser directly

This one is for the adventurous. Inside a route, `import js` gives
your Python code the browser itself: the window size, the page
elements, and a `Canvas` you can draw on with the browser's own
drawing calls. A `Page` can also carry a small `js` or `css` string
to run when it renders.

```python
@route
def inspect(state: State) -> Page:
    import js
    state.report = "Your window is " + str(js.window.innerWidth) + " wide."
    return index(state)
```

Most projects that think they need this actually need a component
they have not met yet. Check the
[component list](../reference/components/index.md) first.

**Look it up**: [JavaScript interop](../extend/javascript.md) and
[Canvas](../reference/components/media/canvas.md).

## Test it, freeze it, and ship it

These are not flashy, but they make a project feel professional and
they save time near the deadline.

- `assert_state` and `assert_has` check a route's result in one
  line, and the debug panel shows which tests passed.
- The debug panel's History tab records every page your app
  produced. You can copy a page you like as a ready-made test, so
  any later change that breaks it fails a test instead of surprising
  you.

**Look it up**: [Test a feature](../add/test-a-feature.md) and
[Freeze finished pages](../add/freeze-pages.md).

## Combine two features

The most memorable projects mix two of the sections above. A few
combinations to start your thinking:

| Idea                         | Features it combines                        |
| ---------------------------- | ------------------------------------------- |
| Photo booth with a countdown | Camera, Timer, Picture transforms, Download |
| Scavenger hunt               | Map, CurrentLocation, ProgressBar           |
| Rhythm game                  | Melody, Clock, Fragment                     |
| Voice-memo diary             | AudioRecorder, DateInput, Table, Download   |
| Study timer with a chart     | Timer, MatPlotLibPlot, Meter                |
| Clap-controlled slideshow    | Microphone, Clock, Image                    |
| Mood tracker                 | DateInput, Table, MatPlotLibPlot, a theme   |
| Pixel-art studio             | Picture.new, set_pixel, Download            |

Pick one feature as the heart of the project and build it first. Add
the second feature only after the first works end to end.
[Choose a manageable idea](choose-an-idea.md) explains how to keep
the scope under control.

## What Drafter cannot do

Knowing the limits early saves you from a dead end halfway through.
All of these come from one fact: your whole app runs inside the
visitor's browser tab.

- **No real accounts or passwords.** Everything is visible to the
  visitor, so a login can shape the flow but protects nothing. A
  clearly labeled login *simulation* is fine.
- **No multiplayer or shared data.** Each visitor runs their own
  copy. Two people cannot see the same chat or leaderboard. "Pass
  the laptop" turn-taking works well instead.

The [project ideas that teachers see](../teach/project-ideas.md)
lists the same limits from the other side of the desk.

## Working with an AI assistant

Your course allows you to use an AI assistant while you program.
Used well, it makes the features on this page reachable in an
afternoon. A few habits make the difference:

- **Give it the real documentation.** Paste the link to the
  reference page for the component you want. Assistants sometimes
  invent parameters or components that do not exist. The reference
  page is the truth.
- **Ask for one small step at a time.** "Add a Camera to the index
  page and show the photo on a second page" works better than "build
  my whole photo app".
- **Paste the exact error.** The debug panel and the terminal show
  the full message. Copy all of it into the chat.
- **Ask it to explain the code it wrote**, line by line, until you
  could rewrite it yourself. You will be the one presenting the
  project.
- **Remind it where the app runs.** If it suggests a database, a
  Flask server, sockets, or threads, that advice is for a different
  kind of program. Say "this is a Drafter app that runs in the
  browser" and it will usually correct course.
- **Keep your tests.** Ask the assistant to write an `assert_state`
  or `assert_has` test for each feature it adds, and run them before
  moving on.

## Common problems

- **The feature works on your laptop but not on your phone.** The
  camera, microphone, and location all need permission, and some
  phone browsers are stricter. Your route should handle a refusal
  (check the `status` or a `None` value) rather than assume a yes.
- **The sound does not play on the first page.** Browsers refuse
  to play audio before the visitor has clicked something. Put the
  sound behind a "Start" button.
- **The timer restarts every time you click.** Each click rebuilds
  the page, including the timer. Answer with a `Fragment` or mark
  the timer `persistent=True`.
- **The map is blank.** The map images need an internet
  connection. Clicks and markers still work.
- **An AI assistant gave you code with `Flask`, `sqlite3`, or `threading`.** Those do not run in the browser. Ask again with the
  link to this page.

## You are ready for the next step when

You can name two features from this page that you want in your
project, and you can say which one you will build first. Then go
[choose a manageable idea](choose-an-idea.md).
